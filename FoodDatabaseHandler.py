import string
import sqlite3
import json
import os

class RecipeDatabaseHandler:
    def __init__(self):
        self.db_path = os.getenv('RECIPE_FILE_KEY')

    def clean_recipe_name(self, recipe_name):
        recipe_name = recipe_name.lower()
        recipe_name = recipe_name.translate(str.maketrans("", "", string.punctuation))
        words = recipe_name.split()
        words = [word for word in words if any(c.isalpha() for c in word)]
        cleaned_words = [word[:-1] if word.endswith('s') and len(word) > 1 else word for word in words]
        cleaned_words = list(set(cleaned_words))
        return cleaned_words

    def search_recipe(self, recipe_name):
        search_query = self.clean_recipe_name(recipe_name)
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

    def get_paginated_recipe(self, recipe_name, page=1, results_per_page=10):
        all_rows = self.search_recipe(recipe_name)
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
    
    def get_recipe_by_id(self, recipe_id):
        try:
            conn = sqlite3.connect(self.db_path)
            curr = conn.cursor()

            query = """
                SELECT *
                FROM recipes
                WHERE id = ?
            """
            curr.execute(query, (recipe_id,))
            row = curr.fetchone()

            return [row] if row else None

        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    
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
                    "time": row[3],
                    "calories": row[9],
                    "image_url" : "https://api.quantumgrove.tech:8001/calosync/xxhdpi/fi_alcohol.png"
                }
                result.append(recipe)

            return result if result else None
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_paginated_all_recipes(self, page=1, results_per_page=10):
        all_rows = self.get_all_recipes()
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
    

    # def get_filtered_recipes(self, filters={}):
    #     try:
    #         conn = sqlite3.connect(self.db_path)
    #         curr = conn.cursor()

    #         base_query = """
    #             SELECT r.id, r.title, r.category, r.time, r.procedures, r.notes, 
    #                 r.dietType, r.serving_size, r.servings_per_recipe, r.calories, 
    #                 r.calories_from_fat, r.total_fat, r.saturated_fat, r.cholesterol, 
    #                 r.sodium, r.total_carbohydrates, r.dietary_fiber, r.sugars, 
    #                 r.protein, r.vitamin_a, r.vitamin_c, r.calcium, r.iron, 
    #                 r.ingredients, r.titleTags, c.countries, 
    #                 GROUP_CONCAT(DISTINCT i.name) AS ingredients_list
    #             FROM recipes r
    #             LEFT JOIN countries_recipes cr ON r.id = cr.recipe_id
    #             LEFT JOIN countries c ON cr.country_id = c.id
    #             LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
    #             LEFT JOIN ingredients i ON ri.ingredient_id = i.id
    #         """

    #         conditions = []
    #         params = []

    #         if "category" in filters:
    #             conditions.append("r.category = ?")
    #             params.append(filters["category"])

    #         if "country" in filters:
    #             conditions.append("c.countries = ?")
    #             params.append(filters["country"])

    #         if "dietType" in filters:
    #             conditions.append("r.dietType LIKE ?")
    #             params.append(f"%{filters['dietType']}%")

    #         if "calories_min" in filters:
    #             conditions.append("r.calories >= ?")
    #             params.append(filters["calories_min"])

    #         if "calories_max" in filters:
    #             conditions.append("r.calories <= ?")
    #             params.append(filters["calories_max"])

    #         if "time_min" in filters:
    #             conditions.append("r.time >= ?")
    #             params.append(filters["time_min"])

    #         if "time_max" in filters:
    #             conditions.append("r.time <= ?")
    #             params.append(filters["time_max"])

    #         if conditions:
    #             base_query += " WHERE " + " AND ".join(conditions)

    #         base_query += " GROUP BY r.id"

    #         curr.execute(base_query, params)
    #         rows = curr.fetchall()

    #         result = []
    #         for row in rows:
    #             recipe = {
    #                 "id": row[0],
    #                 "title": row[1],
    #                 "time": row[3],
    #                 "calories": row[9]
    #             }
    #             result.append(recipe)

    #         return result if result else None

    #     except sqlite3.Error as e:
    #         print(f"Database error: {e}")
    #         return None
    #     finally:
    #         if conn:
    #             conn.close()

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
                    r.ingredients, r.titleTags, 
                    GROUP_CONCAT(DISTINCT c.countries) AS countries, 
                    GROUP_CONCAT(DISTINCT i.name) AS ingredients_list
                FROM recipes r
                LEFT JOIN countries_recipes cr ON r.id = cr.recipe_id
                LEFT JOIN countries c          ON cr.country_id = c.id
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i        ON ri.ingredient_id = i.id
            """

            conditions = []
            params     = []

            if "category" in filters:
                cats = filters["category"]
                if not isinstance(cats, (list, tuple)):
                    cats = [cats]
                placeholders = ",".join("?" for _ in cats)
                conditions.append(f"r.category IN ({placeholders})")
                params.extend(cats)

            if "country" in filters:
                countries = filters["country"]
                if not isinstance(countries, (list, tuple)):
                    countries = [countries]
                placeholders = ",".join("?" for _ in countries)
                conditions.append(f"c.countries IN ({placeholders})")
                params.extend(countries)

            if "dietType" in filters:
                dts = filters["dietType"]
                if not isinstance(dts, (list, tuple)):
                    dts = [dts]
                dt_clauses = []
                for dt in dts:
                    dt_clauses.append("r.dietType LIKE ?")
                    params.append(f"%{dt}%")
                conditions.append("(" + " OR ".join(dt_clauses) + ")")

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

            result = [
                {"id": row[0], "title": row[1], "time": row[3], "calories": row[9], "image_url" : "https://api.quantumgrove.tech:8001/calosync/xxhdpi/fi_alcohol.png"}
                for row in rows
            ]
            return result or None

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

        finally:
            conn.close()
    
    def get_unique_recipes_by_diet_types(self, limit=10):
        diet_types = self.get_all_dietType() or []
        result = []

        for dt in diet_types:
            recipes = self.get_filtered_recipes({"dietType": dt}) or []

            recipes.sort(key=lambda r: len(r.get("dietType", [])))

            total = len(recipes)
            sliced = recipes[:limit]

            result.append({
                "diet_type": dt,
                "recipe_count": total,
                "recipes": sliced
            })

        return result
    

    def get_paginated_filtered_recipes(self, filters={}, page=1, results_per_page=10):
        all_rows = self.get_filtered_recipes(filters)
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
    
    # def get_unique_recipes_by_diet_types(self, limit=10):
    #     diet_types = self.get_all_dietType() or []
    #     result = {}

    #     for dt in diet_types:
    #         recipes = self.get_filtered_recipes({"dietType": dt})
    #         if not recipes:
    #             result[dt] = []
    #             continue
    #         recipes.sort(key=lambda r: len(r.get("dietType", [])))
    #         result[dt] = {"recipes" : recipes[:limit] , "total_len" : len(recipes)}

    #     return result

if __name__ == "__main__":
    pass
