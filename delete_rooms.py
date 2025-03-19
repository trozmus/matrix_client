import requests
from tqdm import tqdm
import json


class SynapseRoomManager:
    def __init__(self, server_url, admin_token):
        self.server_url = server_url.rstrip("/")
        self.admin_token = admin_token
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}

    def get_room_id_by_name(self, room_name):
        """Find the room ID based on its name."""
        url = f"{self.server_url}/_synapse/admin/v1/rooms"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            rooms = response.json().get("rooms", [])
            for room in rooms:
                if room.get("name") == room_name:
                    return room["room_id"]
            print(f"Room '{room_name}' not found.")
            return None
        else:
            print("Error fetching rooms:", response.text)
            return None

    def list_all_rooms(self):
        """List all rooms on the server."""
        url = f"{self.server_url}/_synapse/admin/v1/rooms?limit=500"
        response = requests.get(url, headers=self.headers)
        ret = []
        if response.status_code == 200:
            rooms = response.json().get("rooms", [])
            for room in rooms:
                if "@user.00" in room["creator"]:
                    ret.append(room['room_id'])
            return ret
        else:
            print("Error fetching rooms:", response.text)
            return None

    def remove_all_users(self, room_id):
        """Remove all users from a room before deletion."""
        url = f"{self.server_url}/_synapse/admin/v1/rooms/{room_id}/remove"
        response = requests.post(url, headers=self.headers)
        return response.status_code == 200

    def leave_room(self, room_id):
        """Leave a room (admin must leave before deletion)."""
        url = f"{self.server_url}/_matrix/client/v3/rooms/{room_id}/leave"
        response = requests.post(url, headers=self.headers)
        return response.status_code == 200

    def delete_room(self, room_id):
        """Deletes a room permanently."""
        url = f"{self.server_url}/_synapse/admin/v1/rooms/{room_id}"
        response = requests.delete(
            url, headers=self.headers, json={"purge": True})

        if response.status_code == 200:
            return True
        else:
            print(f"Error deleting room {room_id}: {response.text}")
            return False

    def delete_room_by_name_or_id(self, room_name_or_id):
        """Delete a room using either its name or ID."""
        if room_name_or_id.startswith("!"):  # Check if it's an ID
            room_id = room_name_or_id
        else:
            room_id = self.get_room_id_by_name(room_name_or_id)
            if not room_id:
                return False

        # print(f"Deleting room: {room_id}")

        # Step 1: Remove all users
        # print("Removing users...")
        self.remove_all_users(room_id)

        # Step 2: Leave the room
        # print("Leaving room...")
        self.leave_room(room_id)

        # Step 3: Delete the room
        return self.delete_room(room_id)


# Example usage
server_url = "https://connect.mudita.com"
admin_token = "syt_dHJvem11c2FkbQ_uJyDvNYzWNwzEcrkJYfF_3O5mDm"
room_manager = SynapseRoomManager(server_url, admin_token)


room_to_delete = room_manager.list_all_rooms()
for room_id in tqdm(room_to_delete):
    # Delete a room by name
    # room_manager.delete_room_by_name_or_id("Room 1")

    # Delete a room by ID
    # print(room_id)
    room_manager.delete_room_by_name_or_id(room_id)
