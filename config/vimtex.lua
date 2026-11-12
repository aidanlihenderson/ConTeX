-- Merge before your existing lazy.nvim setup; keep just one VimTeX entry.
vim.g.maplocalleader = "\\"
vim.g.tex_flavor = "latex"
vim.g.vimtex_view_method = "skim"
vim.g.vimtex_compiler_method = "latexmk"
vim.g.vimtex_compiler_latexmk_engines = { ["_"] = "-lualatex" }
vim.g.vimtex_compiler_latexmk = { out_dir = "build" }
vim.opt.conceallevel = 0
-- In require("lazy").setup({...}), retain:
-- { "lervag/vimtex", lazy = false },
