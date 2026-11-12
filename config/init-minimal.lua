-- Optional full minimal init.lua. Back up your current file before adopting it.
vim.opt.number = true
vim.opt.expandtab = true
vim.opt.shiftwidth = 2
vim.opt.tabstop = 2
vim.cmd("filetype plugin indent on")
vim.cmd("syntax enable")
local library = vim.env.LATEX_LIBRARY or vim.fn.expand("~/Code/ConTeX")
dofile(library .. "/config/vimtex.lua")
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  local result = vim.fn.system({
    "git", "clone", "--filter=blob:none", "--branch=stable",
    "https://github.com/folke/lazy.nvim.git", lazypath,
  })
  if vim.v.shell_error ~= 0 then error("lazy.nvim installation failed:\n" .. result) end
end
vim.opt.rtp:prepend(lazypath)
require("lazy").setup({ { "lervag/vimtex", lazy = false } })
