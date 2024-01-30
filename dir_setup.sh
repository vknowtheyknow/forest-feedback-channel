mkdir image_buffer
mkdir image_buffer/imported
mkdir image_buffer/interested
mkdir image_buffer/interested/queue
mkdir image_buffer/disinterested
mkdir image_buffer/segmented
mkdir image_buffer/exported
touch image_buffer/camera_files_map
touch image_buffer/camera_status
echo "0
0" > image_buffer/camera_status
touch lora_transmitter/lora_status
echo "0
0" > lora_transmitter/lora_status
touch lora_receiver/lora_status
echo "0
0" > lora_receiver/lora_status

mkdir service_packet_buffer

mkdir service_packet_buffer/tx
mkdir service_packet_buffer/tx/transmitted

mkdir service_packet_buffer/rx
mkdir service_packet_buffer/rx/rx
mkdir service_packet_buffer/rx/rx/uploaded
mkdir service_packet_buffer/rx/received
mkdir service_packet_buffer/rx/received/uploaded

mkdir lora_receiver/rx_buffer
mkdir lora_receiver/rx_buffer/uploaded

echo "Done"
