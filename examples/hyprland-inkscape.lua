-- Inkscape: abrir as janelas no workspace 5 (mude para "6" se preferir).
-- Hyprland >= 0.55, configuração Lua.
hl.window_rule({
	name = "inkscape-workspace",
	match = { class = ".*[Ii]nkscape.*" },
	workspace = "5",
})

-- Editor de texto/LaTeX: janela pequena, sem dividir o espaço do Inkscape.
hl.window_rule({
	name = "figure-text-editor",
	match = { class = "^kitty-figure-editor$" },
	float = true,
	center = true,
	size = { "800", "300" },
})
