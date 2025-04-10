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

@app.get("/recipes")
async def get_all_recipes():
    try:
        rows = db_handler_recipe.get_all_recipes()
        return {"total_rows": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recipes: {e}")

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

@app.get("/recipes_filter")
async def recipes_filter(
    category: Optional[str] = Query(None, description="Filter by recipe category"),
    country: Optional[str] = Query(None, description="Filter by country of origin"),
    dietType: Optional[str] = Query(None, description="Filter by diet type"),
    calories_min: Optional[int] = Query(None, ge=0, description="Minimum calorie count"),
    calories_max: Optional[int] = Query(None, ge=0, description="Maximum calorie count"),
    time_min: Optional[int] = Query(None, ge=0, description="Minimum cooking time in minutes"),
    time_max: Optional[int] = Query(None, ge=0, description="Maximum cooking time in minutes")
):
    filters = {}
    if category:
        filters["category"] = category
    if country:
        filters["country"] = country
    if dietType:
        filters["dietType"] = dietType
    if calories_min is not None:
        filters["calories_min"] = calories_min
    if calories_max is not None:
        filters["calories_max"] = calories_max
    if time_min is not None:
        filters["time_min"] = time_min
    if time_max is not None:
        filters["time_max"] = time_max

    try:
        results = db_handler_recipe.get_filtered_recipes(filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not results:
        raise HTTPException(status_code=404, detail="No recipes found matching the filters")
    
    return results

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
