-- Inkscape: abrir as janelas no workspace 5 (mude para "6" se preferir).
-- Hyprland >= 0.55, configuração Lua.
hl.window_rule({
    name = "inkscape-workspace",
    match = { class = ".*[Ii]nkscape.*" },
    workspace = "5",
})
