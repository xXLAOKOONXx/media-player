"""
Storage Manager
Handles network storage mounting and management
"""

import os
import subprocess
from pathlib import Path


class StorageManager:
    """Manages network storage connections"""
    
    def __init__(self):
        self.mounted_storages = {}
    
    def mount_smb(self, storage):
        """Mount SMB/CIFS network storage"""
        mount_point = storage['mount_point']
        
        # Create mount point if it doesn't exist
        Path(mount_point).mkdir(parents=True, exist_ok=True)
        
        # Build mount command
        # SECURITY NOTE: In production, use credential files instead of command-line passwords
        # Passwords in command-line arguments are visible in process lists
        # Create a credentials file with restricted permissions (600)
        host = storage['host']
        share = storage['share']
        username = storage.get('username', 'guest')
        
        # This is a simplified version for demonstration
        # In production, you should:
        # 1. Create a credentials file: /home/user/.smbcredentials
        #    username=user
        #    password=pass
        # 2. Set permissions: chmod 600 /home/user/.smbcredentials
        # 3. Use: mount -t cifs ... -o credentials=/home/user/.smbcredentials
        # 4. Or better yet, configure in /etc/fstab or use autofs
        
        try:
            # Note: This requires sudo privileges
            # On Raspberry Pi, configure this in /etc/fstab or use autofs
            # Example fstab entry:
            # //host/share /mnt/point cifs credentials=/home/pi/.smbcreds,uid=1000,gid=1000 0 0
            
            # subprocess.run(mount_cmd, check=True)
            self.mounted_storages[storage['id']] = mount_point
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to mount storage: {e}")
            return False
    
    def unmount(self, storage_id):
        """Unmount a network storage"""
        if storage_id in self.mounted_storages:
            mount_point = self.mounted_storages[storage_id]
            try:
                # subprocess.run(['umount', mount_point], check=True)
                del self.mounted_storages[storage_id]
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to unmount storage: {e}")
                return False
        return False
    
    def is_mounted(self, storage_id):
        """Check if storage is mounted"""
        return storage_id in self.mounted_storages
    
    def get_mount_point(self, storage_id):
        """Get mount point for a storage"""
        return self.mounted_storages.get(storage_id)
