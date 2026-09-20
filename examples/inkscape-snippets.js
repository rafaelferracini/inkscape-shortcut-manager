// LaTeX Suite — Obsidian Desktop, Linux.
// Digite figure: nome da figura e pressione Tab, fora de fórmulas.
// Para editar, selecione ![[figures/nome-da-figura.svg]] e pressione Ctrl+Alt+i.

const FIGURES_DIR = "figures";
const INKSCAPE = "/home/rafaelf/scripts/inkscape-shortcut-manager/inkscape-managed";

function openFigure(relativePath, create) {
    const { Notice } = require("obsidian");
    try {
        const fs = require("fs");
        const path = require("path");
        const { spawn } = require("child_process");
        const adapter = app.vault.adapter;
        if (typeof adapter.getBasePath !== "function") {
            throw new Error("Este snippet requer o Obsidian Desktop e um vault local.");
        }
        const root = adapter.getBasePath();
        const fullPath = path.resolve(root, relativePath);
        const relative = path.relative(root, fullPath);
        if (relative.startsWith(".." + path.sep) || relative === ".." || path.isAbsolute(relative)) {
            throw new Error("A figura precisa estar dentro do vault.");
        }

        if (create) {
            fs.mkdirSync(path.dirname(fullPath), { recursive: true });
            try {
                fs.writeFileSync(fullPath,
                    '<?xml version="1.0" encoding="UTF-8"?>\n' +
                    '<svg xmlns="http://www.w3.org/2000/svg" width="240mm" height="120mm" viewBox="0 0 240 120">\n' +
                    '  <defs/>\n  <g id="layer1"/>\n</svg>\n',
                    { encoding: "utf8", flag: "wx" });
            } catch (error) {
                if (error.code !== "EEXIST") throw error;
            }
        }
        if (!fs.statSync(fullPath).isFile()) throw new Error("O caminho não é um arquivo SVG.");

        const child = spawn(INKSCAPE, [fullPath], {
            detached: true,
            stdio: "ignore",
            shell: false,
        });
        child.on("error", error => new Notice("Não foi possível abrir o Inkscape: " + error.message));
        child.unref();
        return true;
    } catch (error) {
        new Notice("Figura: " + error.message);
        return false;
    }
}

export default [
    {
        trigger: /figure: ([^\n]+)/,
        options: "rt",
        description: "Criar ou abrir uma figura no Inkscape",
        replacement: match => {
            const name = match[1].trim().toLowerCase()
                .replace(/\s+/g, "-");
            // Mantém nomes compatíveis com links do Obsidian e com snippets.
            if (!name || !/^[\p{L}\p{N}_-]+$/u.test(name)) {
                const { Notice } = require("obsidian");
                new Notice("Use letras, números, espaços, hífens ou sublinhados no nome da figura.");
                return false;
            }
            const relativePath = FIGURES_DIR + "/" + name + ".svg";
            if (!openFigure(relativePath, true)) return false;
            return "![[" + relativePath + "]]";
        },
    },
    {
        triggerKey: "Ctrl-Alt-i",
        options: "tv",
        description: "Editar a figura SVG selecionada no Inkscape",
        replacement: selection => {
            const match = /^!\[\[(figures\/[\p{L}\p{N}_-]+\.svg)\]\]$/u.exec(selection.trim());
            if (!match) return false;
            if (!openFigure(match[1], false)) return false;
            return selection;
        },
    },
];
