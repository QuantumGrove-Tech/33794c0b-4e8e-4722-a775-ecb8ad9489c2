import string
import sqlite3
import json

def clean_query(query):
    query = query.lower()
    query = query.translate(str.maketrans("", "", string.punctuation))
    words = query.split()
    cleaned_words = [word[:-1] if word.endswith('s') and len(word) > 1 else word for word in words]
    cleaned_words = list(set(cleaned_words))  
    return cleaned_words

class FoodDatabaseHandler:
    def __init__(self):
        self.db_path = "db/food_nutrition_s3.db"
    
    def search(self, query, page=1, results_per_page=100):
        cleaned_words = clean_query(query)
        if not cleaned_words:
            return None

        intersect_queries = []
        params = []
        for word in cleaned_words:
            intersect_queries.append("SELECT id FROM foodNutrient_fts WHERE nameKeys LIKE ?")
            params.append(f"%{word}%")
        
        if not intersect_queries:
            return None

        intersect_sql = " INTERSECT ".join(intersect_queries)
        common_ids_subquery = f"({intersect_sql})"

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  
            curr = conn.cursor()

            curr.execute(f"SELECT * FROM foodNutrient LIMIT 1")
            columns = [description[0] for description in curr.description]

            count_sql = f"SELECT COUNT(*) FROM {common_ids_subquery}"
            curr.execute(count_sql, params)
            total_rows = curr.fetchone()[0]
            if total_rows == 0:
                return None

            offset = (page - 1) * results_per_page

            data_sql = f"""
            SELECT fn.*
            FROM foodNutrient fn
            JOIN {common_ids_subquery} common_ids ON fn.id = common_ids.id
            ORDER BY 
                CASE WHEN fn.country = 'USA' THEN 1 ELSE 2 END,
                fn.country,
                LENGTH(fn.name)
            LIMIT ? OFFSET ?
            """
            data_params = params + [results_per_page, offset]

            curr.execute(data_sql, data_params)
            rows = curr.fetchall()

            formatted_rows = []
            for row in rows:
                row_dict = {}
                for col in columns:
                    if col == 'serving':
                        row_dict[col] = json.loads(row[col]) if row[col] else []
                    else:
                        row_dict[col] = row[col]
                formatted_rows.append(row_dict)

            return {
                'total_rows': total_rows,
                'page': page,
                'results_per_page': results_per_page,
                'rows': formatted_rows
            }

        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()

class RecipeDatabaseHandler:
    def __init__(self):
        self.db_path = "db/recipes_s3.db"

    def search(self, query=None, filters=None, page=1, results_per_page=100):
        cleaned_words = clean_query(query) if query else None
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            intersect_queries = []
            keyword_params = []
            if cleaned_words:
                for word in cleaned_words:
                    intersect_queries.append("SELECT id FROM recipes WHERE titleTags LIKE ?")
                    keyword_params.append(f"%{word}%")
                intersect_sql = " INTERSECT ".join(intersect_queries)
                common_ids_subquery = f"({intersect_sql})"
            else:
                common_ids_subquery = "(SELECT id FROM recipes)"

            conditions = []
            filter_params = []
            if filters:
                if "category" in filters:
                    cats = filters["category"]
                    if not isinstance(cats, (list, tuple)):
                        cats = [cats]
                    placeholders = ",".join("?" for _ in cats)
                    conditions.append(f"r.category IN ({placeholders})")
                    filter_params.extend(cats)

                if "country" in filters:
                    countries = filters["country"]
                    if not isinstance(countries, (list, tuple)):
                        countries = [countries]
                    placeholders = ",".join("?" for _ in countries)
                    conditions.append(f"c.countries IN ({placeholders})")
                    filter_params.extend(countries)

                if "dietType" in filters:
                    dts = filters["dietType"]
                    if not isinstance(dts, (list, tuple)):
                        dts = [dts]
                    dt_clauses = []
                    for dt in dts:
                        dt_clauses.append("r.dietType LIKE ?")
                        filter_params.append(f"%{dt}%")
                    conditions.append("(" + " OR ".join(dt_clauses) + ")")

                num_filters = [
                    ("calories_min", "r.calories >= ?"),
                    ("calories_max", "r.calories <= ?"),
                    ("time_min", "r.time >= ?"),
                    ("time_max", "r.time <= ?")
                ]
                for key, clause in num_filters:
                    if key in filters:
                        conditions.append(clause)
                        filter_params.append(filters[key])

            all_params = keyword_params + filter_params

            base_query = f"""
                WITH common_ids AS {common_ids_subquery}
                SELECT r.id, r.title, r.time, r.calories
                FROM common_ids
                JOIN recipes r ON common_ids.id = r.id
                LEFT JOIN countries_recipes cr ON r.id = cr.recipe_id
                LEFT JOIN countries c ON cr.country_id = c.id
            """

            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            base_query += " GROUP BY r.id ORDER BY r.title ASC"

            count_query = f"SELECT COUNT(*) FROM ({base_query})"
            curr.execute(count_query, all_params)
            total_rows = curr.fetchone()[0]
            if total_rows == 0:
                return None

            offset = (page - 1) * results_per_page
            data_query = f"{base_query} LIMIT ? OFFSET ?"
            data_params = all_params + [results_per_page, offset]

            curr.execute(data_query, data_params)
            rows = curr.fetchall()

            result = []
            for row in rows:
                recipe = {
                    "id": row[0],
                    "title": row[1],
                    "time": row[2],
                    "calories": row[3],
                    "image_url": "https://api.quantumgrove.tech:8001/calosync/xxhdpi/fi_alcohol.png"
                }
                result.append(recipe)

            return {
                'total_rows': total_rows,
                'page': page,
                'results_per_page': results_per_page,
                'rows': result
            }

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # def search(self, query=None, filters=None, page=1, results_per_page=100):
    #     cleaned_words = clean_query(query) if query else None
    #     try:
    #         conn = sqlite3.connect(self.db_path)
    #         curr = conn.cursor()

    #         intersect_queries = []
    #         keyword_params = []
    #         if cleaned_words:
    #             for word in cleaned_words:
    #                 intersect_queries.append("SELECT id FROM recipes WHERE titleTags LIKE ?")
    #                 keyword_params.append(f"%{word}%")
    #             intersect_sql = " INTERSECT ".join(intersect_queries)
    #             common_ids_subquery = f"({intersect_sql})"
    #         else:
    #             common_ids_subquery = "(SELECT id FROM recipes)"

    #         conditions = []
    #         filter_params = []
    #         or_conditions = []  # To group country and dietType with OR

    #         if filters:
    #             # Handle Category (AND with other filters)
    #             if "category" in filters:
    #                 cats = filters["category"]
    #                 if not isinstance(cats, (list, tuple)):
    #                     cats = [cats]
    #                 placeholders = ",".join("?" for _ in cats)
    #                 conditions.append(f"r.category IN ({placeholders})")
    #                 filter_params.extend(cats)

    #             # Handle Country (part of OR group)
    #             if "country" in filters:
    #                 countries = filters["country"]
    #                 if not isinstance(countries, (list, tuple)):
    #                     countries = [countries]
    #                 placeholders = ",".join("?" for _ in countries)
    #                 or_conditions.append(f"c.countries IN ({placeholders})")
    #                 filter_params.extend(countries)

    #             # Handle DietType (part of OR group)
    #             if "dietType" in filters:
    #                 dts = filters["dietType"]
    #                 if not isinstance(dts, (list, tuple)):
    #                     dts = [dts]
    #                 dt_clauses = []
    #                 for dt in dts:
    #                     dt_clauses.append("r.dietType LIKE ?")
    #                     filter_params.append(f"%{dt}%")
    #                 or_conditions.append("(" + " OR ".join(dt_clauses) + ")")

    #             # Combine country and dietType with OR
    #             if or_conditions:
    #                 conditions.append("(" + " OR ".join(or_conditions) + ")")

    #             # Numerical filters (AND with others)
    #             num_filters = [
    #                 ("calories_min", "r.calories >= ?"),
    #                 ("calories_max", "r.calories <= ?"),
    #                 ("time_min", "r.time >= ?"),
    #                 ("time_max", "r.time <= ?")
    #             ]
    #             for key, clause in num_filters:
    #                 if key in filters:
    #                     conditions.append(clause)
    #                     filter_params.append(filters[key])

    #         all_params = keyword_params + filter_params

    #         base_query = f"""
    #             WITH common_ids AS {common_ids_subquery}
    #             SELECT r.id, r.title, r.time, r.calories
    #             FROM common_ids
    #             JOIN recipes r ON common_ids.id = r.id
    #             LEFT JOIN countries_recipes cr ON r.id = cr.recipe_id
    #             LEFT JOIN countries c ON cr.country_id = c.id
    #         """

    #         if conditions:
    #             base_query += " WHERE " + " AND ".join(conditions)
    #         base_query += " GROUP BY r.id ORDER BY r.title ASC"

    #         count_query = f"SELECT COUNT(*) FROM ({base_query})"
    #         curr.execute(count_query, all_params)
    #         total_rows = curr.fetchone()[0]
    #         if total_rows == 0:
    #             return None

    #         offset = (page - 1) * results_per_page
    #         data_query = f"{base_query} LIMIT ? OFFSET ?"
    #         data_params = all_params + [results_per_page, offset]

    #         curr.execute(data_query, data_params)
    #         rows = curr.fetchall()

    #         result = []
    #         for row in rows:
    #             recipe = {
    #                 "id": row[0],
    #                 "title": row[1],
    #                 "time": row[2],
    #                 "calories": row[3],
    #                 "image_url": "https://api.quantumgrove.tech:8001/calosync/xxhdpi/fi_alcohol.png"
    #             }
    #             result.append(recipe)

    #         return {
    #             'total_rows': total_rows,
    #             'page': page,
    #             'results_per_page': results_per_page,
    #             'rows': result
    #         }

    #     except sqlite3.Error as e:
    #         print(f"Database error: {e}")
    #         return None
    #     finally:
    #         if conn:
    #             conn.close()
    
    def get_all_filters(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()
            filters = {}

            curr.execute("SELECT DISTINCT category FROM recipes WHERE category IS NOT NULL")
            filters['categories'] = [row[0] for row in curr.fetchall()] or None
            curr.execute("SELECT DISTINCT countries FROM countries WHERE countries IS NOT NULL")
            countries = [row[0] for row in curr.fetchall()] or None
            curr.execute("SELECT DISTINCT name FROM categories WHERE name IS NOT NULL")
            filters['dietTypes'] = [row[0] for row in curr.fetchall()] or None
            curr.execute("""
                SELECT MIN(time), MAX(time) 
                FROM recipes 
                WHERE time IS NOT NULL AND time != ''
            """)
            countries_temp = {}
            for country in countries:
                countries_temp[country] = (get_country_code(country))
            filters['countries'] = countries_temp
            time_row = curr.fetchone()
            filters['timeRange'] = (time_row[0], time_row[1]) if time_row else None
            curr.execute("""
                SELECT MIN(calories), MAX(calories)
                FROM recipes
                WHERE calories IS NOT NULL
            """)
            calories_row = curr.fetchone()
            filters['caloriesRange'] = (calories_row[0], calories_row[1]) if calories_row else None

            return filters

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    # def group_recipes_by_diet(self, limit=10):

    #     try:
    #         conn = sqlite3.connect(self.db_path)
    #         curr = conn.cursor()

    #         rows = curr.execute('''
    #             SELECT id, title, time, calories, dietType FROM recipes
    #         ''').fetchall()

    #         data = []
    #         all_diet_types = []

    #         for id, title, time, calories, dietType in rows:
    #             diet_list = json.loads(dietType)
    #             recipe_entry = {
    #                 'id': id,
    #                 'title': title,
    #                 'time': time,
    #                 'calories': calories,
    #                 'dietType': diet_list,
    #                 'image_url': "https://api.quantumgrove.tech:8001/calosync/xxhdpi/fi_alcohol.png",
    #                 'diet_count': len(diet_list) 
    #             }
    #             data.append(recipe_entry)
    #             all_diet_types.extend(diet_list)
    #         all_diet_types = set(all_diet_types)
    #         diet_recipes_all = {diet: {} for diet in all_diet_types}
    #         diet_counts = {diet: 0 for diet in all_diet_types}

    #         for recipe in data:
    #             recipe_id = recipe['id']
    #             for diet in recipe['dietType']:
    #                 diet_counts[diet] += 1  
    #                 if recipe_id not in diet_recipes_all[diet]:
    #                     diet_recipes_all[diet][recipe_id] = recipe

    #         grouped_output = []
    #         for diet in all_diet_types:
    #             sorted_recipes = sorted(diet_recipes_all[diet].values(), key=lambda x: x['diet_count'])
    #             clipped_recipes = [{
    #                 'id': rec['id'],
    #                 'title': rec['title'],
    #                 'time': rec['time'],
    #                 'calories': rec['calories'],
    #                 'image_url': rec['image_url']
    #             } for rec in sorted_recipes[:limit]]
                
    #             grouped_output.append({
    #                 "diet_type": diet,
    #                 "recipe_count": diet_counts[diet],
    #                 "recipes": clipped_recipes
    #             })

    #         return grouped_output
        
    #     except sqlite3.Error as e:
    #         print(f"Database error: {e}")
    #         return None
    #     finally:
    #         if conn:
    #             conn.close()

    def group_recipes_by_diet(self, limit=10):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()
            rows = curr.execute('''
                SELECT id, title, time, calories, dietType, difficulty FROM recipes
            ''').fetchall()
            data = []
            all_diet_types = []
            for id, title, time, calories, dietType, difficulty in rows:
                diet_list = json.loads(dietType)
                recipe_entry = {
                    'id': id,
                    'title': title,
                    'time': time,
                    'calories': calories,
                    'dietType': diet_list,
                    'difficulty' : difficulty,
                    'image_url': "https://api.quantumgrove.tech:8001/calosync/xxhdpi/fi_alcohol.png",
                    'diet_count': len(diet_list)
                }
                data.append(recipe_entry)
                all_diet_types.extend(diet_list)
            all_diet_types = set(all_diet_types)
            diet_recipes_all = {diet: {} for diet in all_diet_types}
            diet_counts = {diet: 0 for diet in all_diet_types}
            for recipe in data:
                recipe_id = recipe['id']
                for diet in recipe['dietType']:
                    diet_counts[diet] += 1
                    if recipe_id not in diet_recipes_all[diet]:
                        diet_recipes_all[diet][recipe_id] = recipe
            grouped_output = []
            for diet in all_diet_types:
                sorted_recipes = sorted(diet_recipes_all[diet].values(), key=lambda x: x['diet_count'])
                clipped_recipes = [{
                    'id': rec['id'],
                    'title': rec['title'],
                    'time': rec['time'],
                    'calories': rec['calories'],
                    'difficulty': rec['difficulty'],
                    'image_url': rec['image_url']
                } for rec in sorted_recipes[:limit]]
                grouped_output.append({
                    "diet_type": diet,
                    "recipe_count": diet_counts[diet],
                    "recipes": clipped_recipes
                })
            return grouped_output
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

        finally:
            if conn:
                conn.close()

    def get_recipe_by_id(self, recipe_id):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            query = """
                SELECT 
                    r.id, r.title, r.category, r.time,
                    r.procedures, r.notes, r.dietType,
                    r.serving_size, r.servings_per_recipe,
                    r.calories, r.calories_from_fat,
                    r.total_fat, r.saturated_fat,
                    r.cholesterol, r.sodium,
                    r.total_carbohydrates, r.dietary_fiber,
                    r.sugars, r.protein,
                    r.vitamin_a, r.vitamin_c,
                    r.calcium, r.iron,
                    r.ingredients, r.titleTags,
                    GROUP_CONCAT(DISTINCT c.countries) AS countries,
                    r.difficulty,
                    r.ingredients
                FROM recipes r
                LEFT JOIN countries_recipes cr ON r.id = cr.recipe_id
                LEFT JOIN countries c ON cr.country_id = c.id
                WHERE r.id = ?
                GROUP BY r.id
            """
            curr.execute(query, (recipe_id,))
            row = curr.fetchone()

            if not row:
                return None

            procedures = json.loads(row[4]) if row[4] else []
            notes = json.loads(row[5]) if row[5] else []
            dietType = json.loads(row[6]) if row[6] else []
            countries = row[25].split(',') if row[25] else []
            ingredients = json.loads(row[27]) if row[27] else []

            return {
                "id": row[0],
                "title": row[1],
                "category": row[2],
                "time": row[3],
                "procedures": procedures,
                "notes": notes,
                "dietType": dietType,  
                "serving_size": row[7],
                "servings_per_recipe": row[8],
                "calories": row[9],
                "calories_from_fat": row[10],
                "total_fat": row[11],
                "saturated_fat": row[12],
                "cholesterol": row[13],
                "sodium": row[14],
                "total_carbohydrates": row[15],
                "dietary_fiber": row[16],
                "sugars": row[17],
                "protein": row[18],
                "vitamin_a": row[19],
                "vitamin_c": row[20],
                "calcium": row[21],
                "iron": row[22],
                "countries": countries,
                "difficulty": row[26],
                "ingredients": ingredients,
                "image_url": "https://api.quantumgrove.tech:8001/calosync/xxhdpi/fi_alcohol.png"
            }

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
        finally:
            if conn:
                conn.close()

import json
from pathlib import Path

def get_country_code(country_name: str) -> str | None:

    _COUNTRY_CODES_PATH = Path("db/country_codes.json")

    with _COUNTRY_CODES_PATH.open(encoding="utf-8") as fp:
        _COUNTRY_CODES = json.load(fp)

    return _COUNTRY_CODES.get(country_name)
    
if __name__ == "__main__":
    pass
