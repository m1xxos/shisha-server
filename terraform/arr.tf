resource "portainer_docker_volume" "downloads" {
  endpoint_id = var.endpoint_id
  name = "downloads"
  driver = "local"

  driver_opts = {
    "type" = "nfs"
    "o" = "addr=192.168.1.138,rw,noatime,rsize=8192,wsize=8192,tcp,timeo=14"
    "device" = "/mnt/main/media/downloads"
  }
}
