from typing import Optional
from fastapi import FastAPI, HTTPException, Query

import os
food_nutrition_file_path = os.getenv('FOOD_NUTRITION_FILE_KEY')
recipe_file_path = os.getenv('RECIPE_FILE_KEY')

app = FastAPI()

from src.dbHelper import FoodDatabaseHandler, RecipeDatabaseHandler

db_handler_food = FoodDatabaseHandler()
db_handler_recipe = RecipeDatabaseHandler()

def return_format(data):
    status = True
    message = "Success"
    return {"status_code": status, "message": message, "response": data}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/search_food_paging")
async def search_food_paging(
    food_name: str = Query(..., alias="food_name"),
    page: int = Query(1, ge=1),
    results_per_page: int = Query(10, ge=1)):
    try:
        result = db_handler_food.search(
            query=food_name,
            page=page,
            results_per_page=results_per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not result:
        raise HTTPException(status_code=404, detail="No results found")
    return return_format(result)

@app.get("/recipe_filters")
async def get_all_filters():
    try:
        filters = db_handler_recipe.get_all_filters()
        if not filters:
            raise HTTPException(status_code=404, detail="No filters found")
        return return_format(filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting filters: {str(e)}")

@app.get("/diet_recommendations")
async def get_diet_recommendations(limit: int = Query(10, description="Maximum number of recipes per diet type")):
    try:
        recommendations = db_handler_recipe.group_recipes_by_diet(limit=limit)
        if not recommendations:
            raise HTTPException(status_code=404, detail="No recommendations found")
        return return_format(recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recipes_filter_paginated")
async def recipes_filter_paginated(
    query: Optional[str] = Query(None, description="Search query"),
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
    filters = {
        k: v for k, v in locals().items() 
        if k not in ["query", "page", "results_per_page"] and v is not None
    }
    
    try:
        result = db_handler_recipe.search(
            query=query,
            filters=filters,
            page=page,
            results_per_page=results_per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not result:
        raise HTTPException(status_code=404, detail="No recipes found matching the criteria")
    return return_format(result)

@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: int):
    try:
        recipe = db_handler_recipe.get_recipe_by_id(recipe_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe with ID {recipe_id} not found")
    return return_format(recipe)

if __name__ == '__main__':
    import uvicorn

    food_missing = not os.path.exists(food_nutrition_file_path)
    recipe_missing = not os.path.exists(recipe_file_path)
    from src.download_s3 import download_db
    if food_missing and recipe_missing:
        download_db(state=None)  
    elif food_missing:
        download_db(state=1)     
    elif recipe_missing:
        download_db(state=2)    
    else:
        print("Both files already exist. No download needed.")

    uvicorn.run("main:app", host='0.0.0.0', port=5000, workers=4, limit_max_requests=200)
