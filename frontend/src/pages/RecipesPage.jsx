/**
 * Provides the searchable recipe book, category management, and recipe editor.
 */
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  ImagePlus,
  Plus,
  Search,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, resourceApi } from "../api";
import { FormModal } from "../components/FormModal";
import { PageHeader } from "../components/PageHeader";

const config = {
  singular: "Recipe",
  fields: [
    { key: "name", label: "Recipe Name", type: "text", required: true },
    { key: "category", label: "Category", type: "text" },
    { key: "servings", label: "Servings", type: "number", step: "1" },
    {
      key: "prep_minutes",
      label: "Prep Time (minutes)",
      type: "number",
      step: "1",
    },
    {
      key: "cook_minutes",
      label: "Cook Time (minutes)",
      type: "number",
      step: "1",
    },
    { key: "ingredients", label: "Ingredients", type: "textarea", wide: true },
    {
      key: "instructions",
      label: "Instructions",
      type: "textarea",
      wide: true,
    },
    { key: "notes", label: "Notes", type: "textarea", wide: true },
  ],
};

export function RecipesPage() {
  const store = useMemo(() => resourceApi("recipes"), []);
  const categoryStore = useMemo(() => resourceApi("recipe-categories"), []);
  const [recipes, setRecipes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [index, setIndex] = useState(0);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState(false);
  const [imageVersion, setImageVersion] = useState(0);

  const load = useCallback(async () => {
    const [rows, categoryRows] = await Promise.all([
      store.list(),
      categoryStore.list(),
    ]);
    setRecipes(rows);
    setCategories(categoryRows);
  }, [categoryStore, store]);

  useEffect(() => {
    load();
  }, [load]);
  const filtered = recipes.filter(
    (recipe) =>
      (category === "All" || recipe.category === category) &&
      recipe.name.toLowerCase().includes(search.toLowerCase()),
  );

  useEffect(() => {
    if (index >= filtered.length) setIndex(Math.max(0, filtered.length - 1));
  }, [filtered.length, index]);

  const recipe = filtered[index];

  async function save(values) {
    if (recipe && editing) await store.update(recipe.id, values);
    else await store.create(values);
    setAdding(false);
    setEditing(false);
    await load();
  }

  async function remove() {
    await store.remove(recipe.id);
    setEditing(false);
    await load();
  }

  async function uploadImage() {
    if (!recipe) return;
    const selected = await api("/recipe-image/select", { method: "POST" });
    if (selected.canceled) return;
    await api(`/recipes/${recipe.id}/image`, {
      method: "PUT",
      body: JSON.stringify(selected),
    });
    setImageVersion((value) => value + 1);
  }

  async function addCategory() {
    const name = window.prompt("New category name");
    if (name?.trim()) {
      await categoryStore.create({ name: name.trim() });
      await load();
    }
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Personal cookbook"
        title="Recipes"
        description="Favorite recipes, collected one page at a time."
        actions={
          <button className="button primary" onClick={() => setAdding(true)}>
            <Plus size={16} /> Add recipe
          </button>
        }
      />
      <div className="recipe-filters">
        <label>
          <span>Category</span>
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option>All</option>
            {categories.map((item) => (
              <option key={item.id}>{item.name}</option>
            ))}
          </select>
        </label>
        <label className="search-field">
          <Search size={17} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search recipes by name"
          />
        </label>
        <button className="button ghost" onClick={addCategory}>
          Add category
        </button>
      </div>
      {recipe ? (
        <article className="recipe-book">
          <div className="book-nav">
            <button
              className="icon-button"
              disabled={index === 0}
              onClick={() => setIndex(index - 1)}
            >
              <ChevronLeft />
            </button>
            <span>
              Recipe {index + 1} of {filtered.length}
            </span>
            <button
              className="icon-button"
              disabled={index === filtered.length - 1}
              onClick={() => setIndex(index + 1)}
            >
              <ChevronRight />
            </button>
          </div>
          <div className="recipe-spread">
            <div className="recipe-photo">
              <RecipeImage recipeId={recipe.id} version={imageVersion} />
              <div className="photo-placeholder">
                <BookOpen size={34} />
                <span>Recipe image</span>
              </div>
              <button className="button ghost image-upload" onClick={uploadImage}>
                <ImagePlus size={16} /> Choose image
              </button>
            </div>
            <div className="recipe-copy">
              <span className="eyebrow">
                {recipe.category || "Uncategorized"}
              </span>
              <h2>{recipe.name}</h2>
              <p className="recipe-meta">
                Serves {recipe.servings || "—"} · Prep{" "}
                {recipe.prep_minutes || 0} min · Cook {recipe.cook_minutes || 0}{" "}
                min
              </p>
              <div className="recipe-sections">
                <RecipeSection title="Ingredients" text={recipe.ingredients} />
                <RecipeSection
                  title="Instructions"
                  text={recipe.instructions}
                />
                <RecipeSection title="Notes" text={recipe.notes} />
              </div>
              <button className="button ghost" onClick={() => setEditing(true)}>
                Edit recipe
              </button>
            </div>
          </div>
        </article>
      ) : (
        <div className="empty-state">
          <strong>No recipes found.</strong>
          <span>Add a recipe or change the filters.</span>
        </div>
      )}
      {adding && (
        <FormModal
          config={config}
          onSave={save}
          onClose={() => setAdding(false)}
        />
      )}
      {editing && recipe && (
        <FormModal
          config={config}
          item={recipe}
          onSave={save}
          onDelete={remove}
          onClose={() => setEditing(false)}
        />
      )}
    </div>
  );
}

function RecipeSection({ title, text }) {
  if (!text) return null;
  return (
    <section>
      <h3>{title}</h3>
      <p>{text}</p>
    </section>
  );
}

function RecipeImage({ recipeId, version }) {
  const [source, setSource] = useState("");

  useEffect(() => {
    api(`/recipes/${recipeId}/image`)
      .then((result) => setSource(result.dataUrl))
      .catch(() => setSource(""));
  }, [recipeId, version]);

  return source ? <img src={source} alt="Recipe" /> : null;
}
