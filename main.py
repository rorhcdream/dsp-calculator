from dataclasses import dataclass
from typing import List, Mapping

import yaml

materials_path = "materials.yaml"
recipes_path = "recipes.yaml"
multipliers_path = "multipliers.yaml"


@dataclass
class Multipliers:
    assembler: Mapping[str, float]
    smelter: Mapping[str, float]
    chemical_plant: Mapping[str, float]


@dataclass
class Recipe:
    input: List["Material"]
    output: List["Material"]
    building: str
    duration: int
    enabled: bool

    @dataclass
    class Material:
        name: str
        amount: int


@dataclass
class UserInput:
    material: str
    production_rate: float
    assembler: str
    smelter: str
    chemical_plant: str
    matrix_lab_height: int


@dataclass
class RequirementForMaterial:
    rate: float
    buildings: Mapping[str, float]


def load_multipliers() -> Multipliers:
    with open(multipliers_path, "r") as file:
        multipliers = yaml.load(file, Loader=yaml.FullLoader)
    return Multipliers(
        assembler={
            material["name"]: material["value"] for material in multipliers["Assembler"]
        },
        smelter={
            material["name"]: material["value"] for material in multipliers["Smelter"]
        },
        chemical_plant={
            material["name"]: material["value"]
            for material in multipliers["Chemical Plant"]
        },
    )


Requirements = Mapping[str, RequirementForMaterial]


def load_recipes() -> List[Recipe]:
    with open(recipes_path, "r") as file:
        recipes = yaml.load(file, Loader=yaml.FullLoader)

    for recipe in recipes:
        recipe["input"] = [Recipe.Material(**material) for material in recipe["input"]]
        recipe["output"] = [
            Recipe.Material(**material) for material in recipe["output"]
        ]

    recipes = [Recipe(**recipe) for recipe in recipes]
    return recipes


def get_user_input() -> UserInput:
    material = input("Enter the material you want to produce: ")
    production_rate = input("Enter the production rate (default - 1): ")
    assembler = input("Enter the assembler (default - Assembling Machine Mk.1): ")
    smelter = input("Enter the smelter (default - Smelter): ")
    chemical_plant = input("Enter the chemical plant (default - Chemical Plant): ")
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
    merged_requirements = {}
    for requirement in requirements:
        for material, requirement_for_material in requirement.items():
            if material in merged_requirements:
                merged_requirements[material].rate += requirement_for_material.rate
                for building, count in requirement_for_material.buildings.items():
                    if building in merged_requirements[material].buildings:
                        merged_requirements[material].buildings[building] += count
                    else:
                        merged_requirements[material].buildings[building] = count
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
        return {target_material: RequirementForMaterial(target_rate, {})}

    recipe = recipe_map[target_material]
    if recipe.building == "Assembler":
        building_multiplier = multipliers.assembler[user_input.assembler]
    elif recipe.building == "Smelter":
        building_multiplier = multipliers.smelter[user_input.smelter]
    elif recipe.building == "Chemical Plant":
        building_multiplier = multipliers.chemical_plant[user_input.chemical_plant]
    elif recipe.building == "Matrix Lab":
        building_multiplier = user_input.matrix_lab_height
    else:
        raise ValueError(f"Invalid building type: {recipe.building}")

    def find_recipe_output_material() -> Recipe.Material:
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
                {
                    recipe.building: target_rate
                    * recipe.duration
                    / output_recipe_material.amount
                    / building_multiplier
                },
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

    for material, requirement in requirements.items():
        print(f"{material}: {requirement.rate}")
        for building, count in requirement.buildings.items():
            print(f"  {building}: {count}")
