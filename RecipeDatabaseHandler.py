import string
import sqlite3
import json

class RecipeDatabaseHandler:
    def __init__(self):
        self.db_path = "recipes_s3.db"

    def clean_food_name(self, food_name):
        food_name = food_name.lower()
        food_name = food_name.translate(str.maketrans("", "", string.punctuation))
        words = food_name.split()
        words = [word for word in words if any(c.isalpha() for c in word)]
        cleaned_words = [word[:-1] if word.endswith('s') and len(word) > 1 else word for word in words]
        cleaned_words = list(set(cleaned_words))
        return cleaned_words

    def search_food(self, food_name):
        search_query = self.clean_food_name(food_name)
        if len(search_query) == 0:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            id_sets = []
            for word in search_query:
                rows = curr.execute(
                    "SELECT id FROM recipes WHERE titleTags LIKE :word", 
                    {"word": f"%{word}%"}
                ).fetchall()
                
                if rows:
                    ids = set(row[0] for row in rows)
                    id_sets.append(ids)
                else:
                    return None

            if id_sets:
                common_ids = set.intersection(*id_sets)
                if not common_ids:
                    return None

                ids_str = ", ".join(str(id) for id in common_ids)
                
                final_query = f"""
                SELECT *
                FROM recipes
                WHERE id IN ({ids_str})
                ORDER BY id
                """

                curr.execute(final_query)
                rows = curr.fetchall()
                return rows if rows else None
            else:
                return None
        except sqlite3.Error as e: 
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_paginated_food(self, food_name, page=1, results_per_page=10):
        all_rows = self.search_food(food_name)
        if all_rows is None:
            return None

        total_rows = len(all_rows)
        start_index = (page - 1) * results_per_page
        end_index = start_index + results_per_page
        page_rows = all_rows[start_index:end_index]
        if not page_rows:
            return None

        return {
            'total_rows': total_rows,
            'page': page,
            'results_per_page': results_per_page,
            'rows': page_rows
        }
    
    def get_all_categories(self):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            curr.execute("SELECT DISTINCT category FROM recipes WHERE category IS NOT NULL")
            rows = curr.fetchall()

            return [row[0] for row in rows] if rows else None
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_countries(self):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            curr.execute("SELECT DISTINCT countries FROM countries WHERE countries IS NOT NULL")
            rows = curr.fetchall()

            return [row[0] for row in rows] if rows else None
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_all_dietType(self):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            curr.execute("SELECT DISTINCT name FROM categories WHERE name IS NOT NULL")
            rows = curr.fetchall()

            return [row[0] for row in rows] if rows else None
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_time_range(self):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            curr.execute("""
                SELECT MIN(time), MAX(time)
                FROM recipes
                WHERE time IS NOT NULL AND time != ''
            """)
            rows = curr.fetchall()

            return rows[0] if rows else None
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_calories_range(self):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            curr.execute("""
                SELECT MIN(calories), MAX(calories)
                FROM recipes
                WHERE calories IS NOT NULL
            """)
            rows = curr.fetchall()

            return rows[0] if rows else None
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()

                
    def get_all_recipes(self):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            curr.execute("""
                SELECT r.id, r.title, r.category, r.time, r.procedures, r.notes, 
                       r.dietType, r.serving_size, r.servings_per_recipe, r.calories, 
                       r.calories_from_fat, r.total_fat, r.saturated_fat, r.cholesterol, 
                       r.sodium, r.total_carbohydrates, r.dietary_fiber, r.sugars, 
                       r.protein, r.vitamin_a, r.vitamin_c, r.calcium, r.iron, 
                       r.ingredients, r.titleTags, c.countries, 
                       GROUP_CONCAT(DISTINCT i.name) AS ingredients_list
                FROM recipes r
                LEFT JOIN countries_recipes cr ON r.id = cr.recipe_id
                LEFT JOIN countries c ON cr.country_id = c.id
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                GROUP BY r.id
            """)

            rows = curr.fetchall()

            result = []
            for row in rows:
                recipe = {
                    "id": row[0],
                    "title": row[1],
                    "category": row[2],
                    "time": row[3],
                    "procedures": json.loads(row[4]) if row[4] else [], 
                    "notes": json.loads(row[5]) if row[5] else [], 
                    "dietType": json.loads(row[6]) if row[6] else [],  
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
                    "ingredients": json.loads(row[23]) if row[23] else [], 
                    "titleTags": row[24],
                    "countries": row[25],
                    "ingredients_list": row[26].split(',') if row[26] else [] 
                }
                result.append(recipe)

            return result if result else None
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    

    def get_filtered_recipes(self, filters={}):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            base_query = """
                SELECT r.id, r.title, r.category, r.time, r.procedures, r.notes, 
                    r.dietType, r.serving_size, r.servings_per_recipe, r.calories, 
                    r.calories_from_fat, r.total_fat, r.saturated_fat, r.cholesterol, 
                    r.sodium, r.total_carbohydrates, r.dietary_fiber, r.sugars, 
                    r.protein, r.vitamin_a, r.vitamin_c, r.calcium, r.iron, 
                    r.ingredients, r.titleTags, c.countries, 
                    GROUP_CONCAT(DISTINCT i.name) AS ingredients_list
                FROM recipes r
                LEFT JOIN countries_recipes cr ON r.id = cr.recipe_id
                LEFT JOIN countries c ON cr.country_id = c.id
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            """

            conditions = []
            params = []

            if "category" in filters:
                conditions.append("r.category = ?")
                params.append(filters["category"])

            if "country" in filters:
                conditions.append("c.countries = ?")
                params.append(filters["country"])

            if "dietType" in filters:
                conditions.append("r.dietType LIKE ?")
                params.append(f"%{filters['dietType']}%")

            if "calories_min" in filters:
                conditions.append("r.calories >= ?")
                params.append(filters["calories_min"])

            if "calories_max" in filters:
                conditions.append("r.calories <= ?")
                params.append(filters["calories_max"])

            if "time_min" in filters:
                conditions.append("r.time >= ?")
                params.append(filters["time_min"])

            if "time_max" in filters:
                conditions.append("r.time <= ?")
                params.append(filters["time_max"])

            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)

            base_query += " GROUP BY r.id"

            curr.execute(base_query, params)
            rows = curr.fetchall()

            result = []
            for row in rows:
                recipe = {
                    "id": row[0],
                    "title": row[1],
                    "category": row[2],
                    "time": row[3],
                    "procedures": json.loads(row[4]) if row[4] else [],
                    "notes": json.loads(row[5]) if row[5] else [],
                    "dietType": json.loads(row[6]) if row[6] else [],
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
                    "ingredients": json.loads(row[23]) if row[23] else [],
                    "titleTags": row[24],
                    "countries": row[25],
                    "ingredients_list": row[26].split(',') if row[26] else []
                }
                result.append(recipe)

            return result if result else None

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    pass
