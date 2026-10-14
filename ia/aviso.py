# Alarma sonora de fin de tanda (la llama tanda.bat después del informe).
import winsound

for _ in range(3):
    winsound.PlaySound(r'C:\Windows\Media\Alarm01.wav', winsound.SND_FILENAME)
