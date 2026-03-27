# Contributing to Intelligent Energy Grid Balancer

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs
1. Search existing [issues](../../issues) first.
2. Open a new issue with a clear title, description, and steps to reproduce.
3. Include your OS, Node.js version, and browser if relevant.

### Suggesting Features
Open an issue with the label `enhancement` and describe your idea, motivation, and proposed implementation.

### Submitting Pull Requests

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```
2. **Install dependencies:**
   ```bash
   npm run install:all
   ```
3. **Make your changes** following the code style below.
4. **Test** that the dev server runs without errors:
   ```bash
   npm run dev
   ```
5. **Commit** with a clear, descriptive message following [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add renewable energy forecast panel
   fix: correct battery discharge calculation
   docs: update API endpoint table
   ```
6. **Push** and open a Pull Request against `main`.

## Code Style

- **JavaScript/JSX**: 2-space indent, single quotes, semicolons.
- **React**: functional components with hooks only.
- **CSS**: TailwindCSS utility classes; minimal custom CSS in `index.css`.
- **Commits**: conventional commits format.

## Development Setup

```bash
npm run install:all   # install all deps
npm run dev           # start backend + frontend concurrently
```

Backend runs on `http://localhost:3001`, frontend on `http://localhost:5173`.

## Questions?

Open an issue or start a [Discussion](../../discussions).
