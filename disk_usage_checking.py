import os
import json
import time
import schedule
from paramiko import SSHClient, MissingHostKeyPolicy, AuthenticationException, SSHException
from dotenv import load_dotenv

load_dotenv()

SSH_USER = os.getenv("SSH_USER")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD")
BACKUP_PASSWORD = os.getenv("BACKUP_PASSWORD")

def main():
    with open("data_site.json", "r") as f:
        response = json.load(f)

    for site in response:
        print(f"---- {site['nojs']} - {site['site']} - {site['ip']} ----")
        print("Attempting to connect with default password.")

        if validate_password(site['ip'], DEFAULT_PASSWORD):
            remote_main(site['ip'], DEFAULT_PASSWORD)
        else:
            print("Default password failed. Trying using raspberry password.")
            if validate_password(site['ip'], BACKUP_PASSWORD):
                print("Using raspberry password.")
                remote_main(site['ip'], BACKUP_PASSWORD)
            else:
                print("Failed to connect with both passwords. Please check the device or VPN Bakti Connection.\n")


def validate_password(ip, password):
    try:
        with create_ssh_client(ip, password) as ssh:
            print("Connection successful with current password.\n")
            return True
    except AuthenticationException:
        print("Authentication failed.")
    except SSHException as e:
        print(f"SSH Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return False


def remote_main(ip, password):
    try:
        with create_ssh_client(ip, password) as ssh:
            # Check disk usage
            print("---- Checking Disk Usage ----")
            stdin, stdout, stderr = ssh.exec_command("df -h")
            resp = stdout.read().decode("utf-8")

            # Extract disk usage percentage
            try:
                use = resp.split("\n")[1].split()[4]
                print(f"Disk Usage: {use}")
                if int(use[:-1]) > 70:
                    print("Disk usage is above 70%.")
                    # Reboot command
                    print("Rebooting device.\n")
                    ssh.exec_command("sudo reboot")
                else:
                    print("Disk usage is below 70%.\n")
            
            except IndexError:
                print("Failed to parse disk usage output.")

    except SSHException as e:
        print(f"SSH command failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    print("\n")


def create_ssh_client(ip, password):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(MissingHostKeyPolicy())
    ssh.load_system_host_keys()
    ssh.connect(ip, username=SSH_USER, password=password)
    return ssh

# Schedule the main function to run every 6 hours
schedule.every(6).hours.do(main)

# Run the scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(1)
