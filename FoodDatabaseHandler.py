import string
import sqlite3

class FoodDatabaseHandler:
    def __init__(self):
        self.db_path = "food_nutrition_s3.db"

    def clean_food_name(self, food_name):
        food_name = food_name.lower()
        food_name = food_name.translate(str.maketrans("", "", string.punctuation))
        words = food_name.split()
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
                    "SELECT id FROM foodNutrient_fts WHERE nameKeys LIKE :word", 
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
                FROM foodNutrient
                WHERE id IN ({ids_str})
                ORDER BY CASE
                    WHEN country = 'USA' THEN 1
                    ELSE 2
                END, country, LENGTH(name) ASC
                LIMIT 100
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
    
if __name__ == "__main__":
    pass
