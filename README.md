# คู่มือการใช้งาน(สำหรับทดสอบ)

## เตรียมการ
- change directory ไปที่หน้าแรกของ repo ```cd ~/lora-multi-tx/```
- activate python venv (บอร์ดพัฒนาใช้คีย์ลัด ```v```)

## ฝั่งส่ง
0. FTP รูปจากกล้อง..
1. จำลองรูปภาพจากกล้อง (เตรียมรูปใน imported) ```./setup```
2. คัดเลือกรูปภาพ (เลือกรูปจาก imported ไปยัง disinterested และ interested/queue) ```python3 ./image_classification```
3. แบ่งรูปภาพเป็นกลุ่มย่อย (นำรูปจาก interested/queue แบ่งไปไว้ที่ segmented และเก็บภาพก่อนแบ่งไว้ด้วยที่ interested) ```python3 ./image_classification/crop.py```
4. ส่งรูปผ่าน LoRa (ย้ายรูปที่ส่งแล้วจาก segmented ไปที่ exported) ```python3 ./image_classification/lora_transmitter```

## ฝั่งรับ
1. สั่งการให้ board LoRa-array เตรียมรับข้อมูลและนำมาเก็บไว้ที่ ./lora_receiver/rx_buffer ```python3 ./lora_receiver/```
2. (สามารถทำงานพร้อม 1.) รวมรูปใน ./lora_receiver/rx_buffer ทั้งรูปย่อยและรูปจริง ```python3 ./lora_receiver/merge.py```
