from __future__ import annotations

from ordocor.data.database import Database


class RecipeRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def categories(self) -> list[str]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT category
                FROM (
                    SELECT name AS category
                    FROM recipe_categories
                    UNION
                    SELECT category
                    FROM recipes
                    WHERE category IS NOT NULL AND TRIM(category) != ''
                )
                ORDER BY category
                """
            ).fetchall()
        return [row["category"] for row in rows]

    def list_recipes(self, category: str, search: str) -> list[dict[str, object]]:
        query = """
            SELECT id, name, category, servings, prep_minutes, cook_minutes,
                   ingredients, instructions, notes, image_data, image_name
            FROM recipes
            WHERE 1 = 1
        """
        parameters: list[object] = []

        if category and category != "All":
            query += " AND category = ?"
            parameters.append(category)
        if search:
            query += " AND name LIKE ?"
            parameters.append(f"%{search}%")
        query += " ORDER BY category, name, id"

        with self.database.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def get(self, recipe_id: int) -> dict[str, object] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, category, servings, prep_minutes, cook_minutes,
                       ingredients, instructions, notes, image_data, image_name
                FROM recipes
                WHERE id = ?
                """,
                (recipe_id,),
            ).fetchone()
        return dict(row) if row else None

    def add(self, recipe: dict[str, object]) -> int:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO recipes (
                    name, category, servings, prep_minutes, cook_minutes,
                    ingredients, instructions, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(recipe),
            )
        return int(cursor.lastrowid)

    def update(self, recipe_id: int, recipe: dict[str, object]) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE recipes
                SET name = ?, category = ?, servings = ?, prep_minutes = ?,
                    cook_minutes = ?, ingredients = ?, instructions = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*self._values(recipe), recipe_id),
            )

    def delete(self, recipe_id: int) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))

    def add_category(self, category: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO recipe_categories (name) VALUES (?)",
                (category,),
            )

    def set_image(self, recipe_id: int, image_data: bytes, image_name: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE recipes
                SET image_data = ?, image_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (image_data, image_name, recipe_id),
            )

    def _values(self, recipe: dict[str, object]) -> tuple[object, ...]:
        return (
            recipe["name"],
            recipe["category"],
            recipe["servings"],
            recipe["prep_minutes"],
            recipe["cook_minutes"],
            recipe["ingredients"],
            recipe["instructions"],
            recipe["notes"],
        )
