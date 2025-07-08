# Twitter bot için çalıştırma betiği
# Her çalışmada benzersiz log dosyası oluştur
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logfile = "botlog_$timestamp.txt"

Write-Output "Başladı: $(Get-Date)" >> $logfile
Set-Location -Path "C:\Users\AA\Desktop\TWITTERBOT\newnew-main - Kopya"
C:\Users\AA\AppData\Local\Programs\Python\Python311\python.exe main.py >> $logfile 2>&1
Write-Output "Bitti: $(Get-Date)" >> $logfile