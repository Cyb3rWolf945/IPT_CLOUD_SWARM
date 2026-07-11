local monitor = peripheral.wrap("top") -- Ajusta para o lado do monitor
monitor.setTextScale(1)
monitor.clear()

local function drawButton(x, y, text, color)
    monitor.setCursorPos(x, y)
    monitor.setBackgroundColor(color)
    monitor.write(" " .. text .. " ")
end

-- Desenhar o painel
drawButton(2, 2, " LIGAR ", colors.green)
drawButton(2, 4, " DESLIGAR ", colors.yellow)
drawButton(2, 6, " DESTRUIR ", colors.red)

while true do
    local event, side, x, y = os.pullEvent("monitor_touch")
    if y == 2 then shell.run("test_trigger_start")
    elseif y == 4 then shell.run("test_trigger_stop")
    elseif y == 6 then shell.run("test_trigger_destroy")
    end
end