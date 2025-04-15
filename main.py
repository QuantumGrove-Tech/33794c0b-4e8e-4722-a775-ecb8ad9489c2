from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from RecipeDatabaseHandler import RecipeDatabaseHandler
from FoodDatabaseHandler import FoodDatabaseHandler

app = FastAPI()
db_handler_food = FoodDatabaseHandler()
db_handler_recipe = RecipeDatabaseHandler()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/categories")
async def get_all_categories():
    try:
        categories = db_handler_recipe.get_all_categories()
        return {"total": len(categories), "categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categories: {e}")

@app.get("/countries")
async def get_all_countries():
    try:
        countries = db_handler_recipe.get_all_countries()
        return {"total": len(countries), "countries": countries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting countries: {e}")

@app.get("/diet_types")
async def get_all_diet_types():
    try:
        diet_types = db_handler_recipe.get_all_dietType()
        return {"total": len(diet_types), "diet_types": diet_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting diet types: {e}")

@app.get("/time_range")
async def get_time_range():
    try:
        time_min, time_max = db_handler_recipe.get_time_range()
        return {"time_min": time_min, "time_max": time_max}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting time range: {e}")

@app.get("/calories_range")
async def get_calories_range():
    try:
        cal_min, cal_max = db_handler_recipe.get_calories_range()
        return {"calories_min": cal_min, "calories_max": cal_max}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting calories range: {e}")

@app.get("/recipes_filter_paginated")
async def recipes_filter_paginated(
    category: Optional[str] = Query(None, description="Filter by recipe category"),
    country: Optional[str] = Query(None, description="Filter by country of origin"),
    dietType: Optional[str] = Query(None, description="Filter by diet type"),
    calories_min: Optional[int] = Query(None, ge=0, description="Minimum calorie count"),
    calories_max: Optional[int] = Query(None, ge=0, description="Maximum calorie count"),
    time_min: Optional[int] = Query(None, ge=0, description="Minimum cooking time in minutes"),
    time_max: Optional[int] = Query(None, ge=0, description="Maximum cooking time in minutes"),
    page: int = Query(1, ge=1, description="Page number (min 1)"),
    results_per_page: int = Query(10, ge=1, le=100, description="Results per page (1-100)")
):
    filters = {k: v for k, v in locals().items() if k not in ["page", "results_per_page"] and v is not None}
    
    try:
        result = db_handler_recipe.get_paginated_filtered_recipes(filters, page, results_per_page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not result:
        raise HTTPException(status_code=404, detail="No recipes found matching the filters")
    return result

@app.get("/recipes_by_diet_types")
async def recipes_by_diet_types(
    limit: int = Query(10, ge=1, le=50, description="Max recipes per diet type (1-50)")
):
    try:
        result = db_handler_recipe.get_unique_recipes_by_diet_types(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not result:
        raise HTTPException(status_code=404, detail="No recipes found for any diet type")
    return result

@app.get("/recipes_all")
async def recipes_all(
    page: int = Query(1, ge=1, description="Page number (min 1)"),
    results_per_page: int = Query(10, ge=1, le=100, description="Results per page (1-100)")
):
    try:
        result = db_handler_recipe.get_paginated_all_recipes(page, results_per_page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not result:
        raise HTTPException(status_code=404, detail="No recipes found")
    return result

@app.get("/recipes/search")
async def search_recipes(
    recipe_name: str = Query(..., description="Recipe name to search for"),
    page: int = Query(1, ge=1, description="Page number (min 1)"),
    results_per_page: int = Query(10, ge=1, le=100, description="Results per page (1-100)")
):
    try:
        result = db_handler_recipe.get_paginated_recipe(recipe_name, page, results_per_page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No recipes found matching '{recipe_name}'")
    return result

@app.get("/recipes/{recipe_id}")
async def get_recipe(
    recipe_id: Optional[int] = Query(default=None, description="ID of the recipe to retrieve")
):
    if recipe_id is None:
        return None 
    try:
        recipe = db_handler_recipe.get_recipe_by_id(recipe_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe with ID {recipe_id} not found")
    return recipe[0]  # Return single recipe object instead of list

@app.get("/search_food_paging")
async def search_food_paging(
    food_name: str = Query(..., alias="food_name"),
    page: int = Query(1, ge=1),
    results_per_page: int = Query(10, ge=1)
):
    result = db_handler_food.get_paginated_food(food_name, page=page, results_per_page=results_per_page)
    if result:
        return {"total_rows": len(result), "rows": result}
    else:
        raise HTTPException(status_code=404, detail="No results found.")

@app.get("/search_food")
async def search_food(food_name: str = Query(..., alias="food_name")):
    result = db_handler_food.search_food(food_name)
    if result:
        return {"total_rows": len(result), "rows": result}
    else:
        raise HTTPException(status_code=404, detail="No results found.")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host='0.0.0.0', port=5000, workers=4, limit_max_requests=200)
