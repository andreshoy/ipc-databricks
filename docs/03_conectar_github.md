# 03 · Conectar este repositorio de GitHub a Databricks

Repositorio: <https://github.com/andreshoy/ipc-databricks> (público)

## A. Clonar el repo en el workspace (solo lectura, sin token)

1. En Databricks ve a **Workspace** → abre tu carpeta de usuario (`/Users/tu-correo`).
2. Clic en **Create** → **Git folder**.
3. En *Git repository URL* pega `https://github.com/andreshoy/ipc-databricks`.
   El proveedor se detecta como **GitHub**. Deja el nombre `ipc-databricks`.
4. Clic en **Create Git folder**. Verás las carpetas `docs`, `notebooks`, `src`, etc.

Para traer cambios nuevos del repo: abre la carpeta → botón con el nombre de la rama (`main`) →
**Pull**.

## B. (Opcional) Poder hacer *commit* y *push* desde Databricks

Si vas a editar notebooks en Databricks y quieres guardarlos en GitHub:

1. En GitHub: **Settings** → **Developer settings** → **Personal access tokens** →
   **Fine-grained tokens** → **Generate new token**.
   - *Repository access*: solo `ipc-databricks`.
   - *Permissions* → *Contents*: **Read and write**.
   - Copia el token (empieza por `github_pat_`). No lo pegues en ningún archivo del repo.
2. En Databricks: clic en tu avatar (arriba a la derecha) → **Settings** → **Linked accounts** →
   **Add Git credential** → proveedor GitHub → pega el token y tu usuario de GitHub.
   (También puede aparecer la opción **Link GitHub account** con OAuth, que es aún más simple.)
3. Ahora en el Git folder puedes **Commit & Push**.

> Recomendación de flujo: edita en tu computador (VS Code), haz `git push`, y en Databricks haz
> **Pull**. Así el repo de GitHub siempre es la fuente de verdad.

## ✅ Checkpoint
En tu workspace existe la carpeta `ipc-databricks` y dentro ves `notebooks/00_setup_catalogo`.
