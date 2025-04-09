from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from RecipeDatabaseHandler import RecipeDatabaseHandler
from FoodDatabaseHandler import FoodDatabaseHandler

app = FastAPI()
db_handler = FoodDatabaseHandler()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/recipes")
async def get_all_recipes():
    rows = db_handler.get_all_recipes()
    return {"total_rows": len(rows), "rows": rows}

@app.get("/categories")
async def get_all_categories():
    categories = db_handler.get_all_categories()
    return {"total": len(categories), "categories": categories}

@app.get("/countries")
async def get_all_countries():
    countries = db_handler.get_all_countries()
    return {"total": len(countries), "countries": countries}

@app.get("/diet_types")
async def get_all_diet_types():
    diet_types = db_handler.get_all_dietType()
    return {"total": len(diet_types), "diet_types": diet_types}

@app.get("/time_range")
async def get_time_range():
    time_min, time_max = db_handler.get_time_range()
    return {"time_min": time_min, "time_max": time_max}

@app.get("/calories_range")
async def get_calories_range():
    cal_min, cal_max = db_handler.get_calories_range()
    return {"calories_min": cal_min, "calories_max": cal_max}

@app.get("/search_food_paging")
async def search_food_paging(
    food_name: str = Query(..., alias="food_name"),
    page: int = Query(1, ge=1),
    results_per_page: int = Query(10, ge=1)
):
    result = db_handler.get_paginated_food(food_name, page=page, results_per_page=results_per_page)
    if result:
        return {"total_rows": len(result), "rows": result}
    raise HTTPException(status_code=404, detail="No results found.")

@app.get("/search_food_paging")
async def search_food_paging(
    food_name: str = Query(..., alias="food_name"),
    page: int = Query(1, ge=1),
    results_per_page: int = Query(10, ge=1)
):
    result = db_handler.get_paginated_food(food_name, page=page, results_per_page=results_per_page)
    if result:
        return {"total_rows": len(result), "rows": result}
    else:
        raise HTTPException(status_code=404, detail="No results found.")

@app.get("/search_food")
async def search_food(food_name: str = Query(..., alias="food_name")):
    result = db_handler.search_food(food_name)
    if result:
        return {"total_rows": len(result), "rows": result}
    else:
        raise HTTPException(status_code=404, detail="No results found.")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host='0.0.0.0', port=5000, workers=4, limit_max_requests=200)
