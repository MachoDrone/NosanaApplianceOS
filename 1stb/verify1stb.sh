# Check if the done marker exists
ls -la /var/lib/nosana/firstboot.done

# Check systemd service status
#sudo systemctl status nosana-firstboot.service

# Check if service is disabled (should be after running)
sudo systemctl is-enabled nosana-firstboot.service

# Check system logs for the service
#sudo journalctl -u nosana-firstboot.service

# Check if the script file still exists
ls -la /usr/local/bin/nosana-firstboot.sh

-----------------------------------------------------------------------

# Check if the service ran at all
sudo systemctl status nosana-firstboot.service

# Check the log file (v0.07.4 adds logging)
sudo cat /var/log/nosana-firstboot.log

# Check journal logs
sudo journalctl -u nosana-firstboot.service -b

# Check if the done file exists
ls -la /var/lib/nosana/
