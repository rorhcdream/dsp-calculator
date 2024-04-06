from dataclasses import dataclass
from typing import List, Mapping

import yaml
from tabulate import tabulate

materials_path = "materials.yaml"
recipes_path = "recipes.yaml"
multipliers_path = "multipliers.yaml"


@dataclass
class Multipliers:
    assembler: Mapping[str, float]
    smelting_facility: Mapping[str, float]
    chemical_facility: Mapping[str, float]


@dataclass
class MaterialWithAmount:
    name: str
    amount: float


@dataclass
class Recipe:
    input: List[MaterialWithAmount]
    output: List[MaterialWithAmount]
    made_in: str
    duration: int
    enabled: bool


@dataclass
class UserInput:
    material: str
    production_rate: float
    assembler: str
    smelting_facility: str
    chemical_facility: str
    matrix_lab_height: int

    def multiplier_for_facility(
        self, multipliers: Multipliers, facility: str,
    ) -> float:
        if facility == "Assembler":
            return multipliers.assembler[self.assembler]
        elif facility == "Smelting Facility":
            return multipliers.smelting_facility[self.smelting_facility]
        elif facility == "Chemical Facility":
            return multipliers.chemical_facility[self.chemical_facility]
        elif facility == "Research Facility":
            return self.matrix_lab_height
        elif facility == "Refining Facility":
            return 1
        else:
            raise ValueError(f"Invalid facility: {facility}")

    def building_for_facility(self, facility: str) -> str:
        if facility == "Assembler":
            return self.assembler
        elif facility == "Smelting Facility":
            return self.smelting_facility
        elif facility == "Chemical Facility":
            return self.chemical_facility
        elif facility == "Research Facility":
            return "Matrix Lab"
        elif facility == "Refining Facility":
            return "Oil Refinery"
        else:
            raise ValueError(f"Invalid facility: {facility}")


@dataclass
class RequirementForMaterial:
    rate: float
    building: MaterialWithAmount


Requirements = Mapping[str, RequirementForMaterial]


def load_multipliers() -> Multipliers:
    with open(multipliers_path, "r") as file:
        multipliers = yaml.load(file, Loader=yaml.FullLoader)
    return Multipliers(
        assembler={
            material["name"]: material["value"] for material in multipliers["Assembler"]
        },
        smelting_facility={
            material["name"]: material["value"]
            for material in multipliers["Smelting Facility"]
        },
        chemical_facility={
            material["name"]: material["value"]
            for material in multipliers["Chemical Facility"]
        },
    )


def load_recipes() -> List[Recipe]:
    with open(recipes_path, "r") as file:
        recipes = yaml.load(file, Loader=yaml.FullLoader)

    for recipe in recipes:
        recipe["input"] = [
            MaterialWithAmount(**material) for material in recipe["input"]
        ]
        recipe["output"] = [
            MaterialWithAmount(**material) for material in recipe["output"]
        ]

    recipes = [Recipe(**recipe) for recipe in recipes]
    return recipes


def get_user_input() -> UserInput:
    material = input("Enter the material you want to produce: ")
    production_rate = input("Enter the production rate (default - 1): ")
    assembler = input("Enter the assembler (default - Assembling Machine Mk.1): ")
    smelter = input("Enter the smelting facility (default - Smelter): ")
    chemical_plant = input("Enter the chemical facility (default - Chemical Plant): ")
    matrix_lab_height = input("Enter the matrix lab height (default - 3): ")

    production_rate = float(production_rate) if production_rate else 1
    assembler = assembler if assembler else "Assembling Machine Mk.1"
    smelter = smelter if smelter else "Smelter"
    chemical_plant = chemical_plant if chemical_plant else "Chemical Plant"
    matrix_lab_height = int(matrix_lab_height) if matrix_lab_height else 3

    return UserInput(
        material,
        production_rate,
        assembler,
        smelter,
        chemical_plant,
        matrix_lab_height,
    )


def build_recipe_map(recipes: List[Recipe]) -> Mapping[str, Recipe]:
    return {
        output.name: recipe
        for recipe in recipes
        for output in recipe.output
        if recipe.enabled
    }


def merge_requirements(
    requirements: List[Mapping[str, RequirementForMaterial]]
) -> Mapping[str, RequirementForMaterial]:
    merged_requirements: Mapping[str, RequirementForMaterial] = {}
    for requirement in requirements:
        for material, requirement_for_material in requirement.items():
            if material in merged_requirements:
                merged_requirements[material].rate += requirement_for_material.rate
                merged_requirements[
                    material
                ].building.name = requirement_for_material.building.name
                merged_requirements[
                    material
                ].building.amount += requirement_for_material.building.amount
            else:
                merged_requirements[material] = requirement_for_material
    return merged_requirements


def get_requirements(
    target_material: str,
    target_rate: float,
    user_input: UserInput,
    recipe_map: Mapping[str, Recipe],
    multipliers: Multipliers,
) -> Requirements:
    if target_material not in recipe_map:
        return {
            target_material: RequirementForMaterial(
                target_rate, MaterialWithAmount(name="", amount=0)
            )
        }

    recipe = recipe_map[target_material]

    def find_recipe_output_material() -> MaterialWithAmount:
        for material in recipe.output:
            if material.name == target_material:
                return material
        raise ValueError(f"Material not found in recipe output: {target_material}")

    output_recipe_material = find_recipe_output_material()

    requirements = [
        get_requirements(
            material.name,
            target_rate / output_recipe_material.amount * material.amount,
            user_input,
            recipe_map,
            multipliers,
        )
        for material in recipe.input
    ]

    requirements.append(
        {
            target_material: RequirementForMaterial(
                target_rate,
                MaterialWithAmount(
                    name=user_input.building_for_facility(recipe.made_in),
                    amount=target_rate
                    * recipe.duration
                    / output_recipe_material.amount
                    / user_input.multiplier_for_facility(multipliers, recipe.made_in),
                ),
            )
        }
    )

    return merge_requirements(requirements)


if __name__ == "__main__":
    recipes = load_recipes()
    multipliers = load_multipliers()
    user_input = get_user_input()

    recipe_map = build_recipe_map(recipes)

    requirements = get_requirements(
        user_input.material,
        user_input.production_rate,
        user_input,
        recipe_map,
        multipliers,
    )

    table = []
    for material, requirement in requirements.items():
        table.append(
            [
                material,
                f"{requirement.rate:.2f}",
                requirement.building.name,
                f"{requirement.building.amount:.2f}"
                if requirement.building.amount != 0
                else "",
            ]
        )
    print(
        tabulate(
            table, headers=["Material", "Rate", "Building", "Count"], numalign="left",
        )
    )
