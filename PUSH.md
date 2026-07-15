# Push

Repo ya inicializado. Commit hecho. Branch `main`.

## 1. Crear el repo vacio en GitHub

https://github.com/new  →  nombre `lambda-spec`, **sin** README, **sin** .gitignore, **sin** licencia.

## 2. Push

```bash
git remote add origin https://github.com/SamySalamy87x/lambda-spec.git
git push -u origin main
```

Eso es todo. El commit ya existe con tus datos de autor.

## 3. Zenodo (DOI nuevo)

1. https://zenodo.org/account/settings/github/ → activa el toggle en `lambda-spec`
2. En GitHub: Releases → Create a new release → tag `v1.1.0`
3. Zenodo dispara DOI automatico al publicar el release
4. En el Zenodo viejo (10.5281/zenodo.20724294) → Edit → Related identifiers →
   `is previous version of` → nuevo DOI

## 4. Badge (opcional, al README)

```markdown
[![DOI](https://zenodo.org/badge/DOI/<nuevo-doi>.svg)](https://doi.org/<nuevo-doi>)
```
