from dataclasses import dataclass
from typing import List, Mapping

import yaml
from tabulate import tabulate

materials_path = "materials.yaml"
recipes_path = "recipes.yaml"
facility_buildings_path = "facility_buildings.yaml"
multipliers_path = "multipliers.yaml"


@dataclass
class FacilityBuildings:
    assembler: List[str]
    smelting_facility: List[str]
    chemical_facility: List[str]
    research_facility: List[str]
    refining_facility: List[str]


@dataclass
class Multipliers:
    assembler: Mapping[str, float]
    smelting_facility: Mapping[str, float]
    chemical_facility: Mapping[str, float]


@dataclass
class MaterialWithAmount:
    name: str = ""
    amount: float = 0

    def __add__(self, other: "MaterialWithAmount") -> "MaterialWithAmount":
        if self.name != other.name:
            raise ValueError("Cannot add materials with different names")
        return MaterialWithAmount(self.name, self.amount + other.amount)

    def __mul__(self, multiplier: float) -> "MaterialWithAmount":
        return MaterialWithAmount(self.name, self.amount * multiplier)

    __rmul__ = __mul__

    def __truediv__(self, divisor: float) -> "MaterialWithAmount":
        return MaterialWithAmount(self.name, self.amount / divisor)


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
    input: List[MaterialWithAmount]


Requirements = Mapping[str, RequirementForMaterial]


def load_materials() -> List[str]:
    with open(materials_path, "r") as file:
        materials = yaml.load(file, Loader=yaml.FullLoader)
    return materials


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


def load_facility_buildings() -> FacilityBuildings:
    with open(facility_buildings_path, "r") as file:
        facility_buildings = yaml.load(file, Loader=yaml.FullLoader)
    return FacilityBuildings(
        assembler=facility_buildings["Assembler"],
        smelting_facility=facility_buildings["Smelting Facility"],
        chemical_facility=facility_buildings["Chemical Facility"],
        research_facility=facility_buildings["Research Facility"],
        refining_facility=facility_buildings["Refining Facility"],
    )


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


def get_user_input(
    materials: List[str], facility_buildings: FacilityBuildings,
) -> UserInput:
    material = input("Enter the material you want to produce: ")
    if material not in materials:
        raise ValueError(f"Invalid material: {material}")

    production_rate = input("Enter the production rate (default - 1): ")
    production_rate = float(production_rate) if production_rate else 1
    if production_rate <= 0:
        raise ValueError("Production rate must be positive")

    assembler = input("Enter the assembler (default - Assembling Machine Mk.1): ")
    assembler = assembler if assembler else "Assembling Machine Mk.1"
    if assembler not in facility_buildings.assembler:
        raise ValueError(f"Invalid assembler: {assembler}")

    smelter = input("Enter the smelting facility (default - Smelter): ")
    smelter = smelter if smelter else "Smelter"
    if smelter not in facility_buildings.smelting_facility:
        raise ValueError(f"Invalid smelting facility: {smelter}")

    chemical_plant = input("Enter the chemical facility (default - Chemical Plant): ")
    chemical_plant = chemical_plant if chemical_plant else "Chemical Plant"
    if chemical_plant not in facility_buildings.chemical_facility:
        raise ValueError(f"Invalid chemical facility: {chemical_plant}")

    matrix_lab_height = input("Enter the matrix lab height (default - 3): ")
    matrix_lab_height = int(matrix_lab_height) if matrix_lab_height else 3
    if matrix_lab_height <= 0:
        raise ValueError("Matrix lab height must be positive")

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
                merged_requirements[material].input = [
                    merged_requirements[material].input[i]
                    + requirement_for_material.input[i]
                    for i in range(len(requirement_for_material.input))
                ]
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
                target_rate, MaterialWithAmount(), input=[],
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
                rate=target_rate,
                building=MaterialWithAmount(
                    name=user_input.building_for_facility(recipe.made_in),
                    amount=target_rate,
                )
                * recipe.duration
                / output_recipe_material.amount
                / user_input.multiplier_for_facility(multipliers, recipe.made_in),
                input=[
                    material * target_rate / output_recipe_material.amount
                    for material in recipe.input
                ],
            )
        }
    )

    return merge_requirements(requirements)


if __name__ == "__main__":
    materials = load_materials()
    recipes = load_recipes()
    facility_buildings = load_facility_buildings()
    multipliers = load_multipliers()

    user_input = get_user_input(materials, facility_buildings)

    recipe_map = build_recipe_map(recipes)

    requirements = get_requirements(
        user_input.material,
        user_input.production_rate,
        user_input,
        recipe_map,
        multipliers,
    )

    def format_float(value: float) -> str:
        return f"{value:.2f}" if value != 0 else ""

    def print_material_table():
        table = []
        max_input = 0
        for material, requirement in requirements.items():
            table.append(
                [
                    material,
                    format_float(requirement.rate),
                    requirement.building.name,
                    format_float(requirement.building.amount),
                ]
            )
            max_input = max(max_input, len(requirement.input))
            for input_material in requirement.input:
                table[-1].extend(
                    [input_material.name, format_float(input_material.amount)]
                )

        headers = ["Material", "Rate", "Building", "Amount"]
        for i in range(max_input):
            headers.extend([f"Input {i + 1}", "Rate"])
        print(tabulate(table, headers=headers, numalign="left"))

    def print_building_table():
        buildings: Mapping[str, MaterialWithAmount] = {}
        for _, requirement in requirements.items():
            if requirement.building.name == "":
                continue
            if requirement.building.name in buildings:
                buildings[requirement.building.name] += requirement.building
            else:
                buildings[requirement.building.name] = requirement.building

        table = [
            [building, format_float(material.amount)]
            for building, material in buildings.items()
        ]

        print(tabulate(table, headers=["Building", "Amount"], numalign="left",))

    print()
    print_material_table()
    print()
    print_building_table()
