from matrix_api import MatrixAPI
import uuid
import csv
import asyncio
import json
import random
from tqdm import tqdm
import config
import helper
import functools
import time


class SynapseClient(MatrixAPI):
    def __init__(self, base_url, logger=None, agent=None):
        super().__init__(base_url)
        self.logger = logger
        self.agent = agent

    async def register_user(self, username, password):
        """Register a new user using m.login.dummy authentication."""
        endpoint = "/_matrix/client/v3/register"
        data = {
            "auth": {"type": "m.login.dummy"},
            "username": username,
            "password": password,
        }
        return await self._request("POST", endpoint, data)

    async def login(self, username, password):
        """Log in and set the access token."""
        endpoint = "/_matrix/client/v3/login"
        data = {
            "type": "m.login.password",
            "user": username,
            "password": password
        }
        ret = await self._request("POST", endpoint, data)
        if ret.status_code == 200:
            response = ret.json()
            self.set_access_token(response["access_token"])
        return ret

    async def list_users(self):
        """Get all users (Admin API)."""
        endpoint = "/_synapse/admin/v2/users"
        return await self._request("GET", endpoint)

    async def list_rooms(self):
        """Get all rooms (Admin API)."""
        endpoint = "/_synapse/admin/v1/rooms"
        return await self._request("GET", endpoint)

    async def create_dm_room(self, invite_user):
        """Create a new dmroom."""
        endpoint = "/_matrix/client/v3/createRoom"
        data = {
            "is_direct": True,
            "preset": "private_chat",
            "invite": [invite_user]
        }
        delay = 1
        retries = 5
        for i in range(retries):
            response = await self._request("POST", endpoint, data)
            if response.status_code == 200:
                return response
            if response.status_code == 429:
                print(f"Rate limited, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                break
        return response

    async def create_room(self, room_name, invite_users=[]):
        """Create a new room."""
        endpoint = "/_matrix/client/v3/createRoom"
        data = {
            "name": room_name,
            "preset": "private_chat",
            "invite": invite_users
        }
        delay = 1
        retries = 5
        for i in range(retries):
            response = await self._request("POST", endpoint, data)
            if response.status_code == 200:
                return response
            if response.status_code == 429:
                print(f"Rate limited, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                break
        return None

    async def invite_users(self, room_id, user):
        endpoint = f"/_matrix/client/v3/rooms/{room_id}/invite"
        data = {"user_id": user}
        delay = 1
        retries = 5
        for i in range(retries):
            response = await self._request("POST", endpoint, data)
            if response.status_code == 200:
                return response
            if response.status_code == 429:
                print(f"Rate limited, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                break
        return None

    async def send_message(self, room_id, message, username, whatsuapp_room):
        """Send a message to a room."""

        start_time = time.time()
        txn_id = str(uuid.uuid4())
        endpoint = f"/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn_id}"
        data = {"msgtype": "m.text", "body": message}
        delay = 1
        retries = 5
        msg_size = len(message)
        for i in range(retries):
            response = await self._request("PUT", endpoint, data)
            if response.status_code == 200:
                end_time = time.time()
                execution_time = round(end_time - start_time, 6)
                log_entry = f"{start_time:0.0f}, {self.agent}, {username},{room_id},{response.status_code},{msg_size},{execution_time}, {whatsuapp_room}"
                self.logger.info(log_entry)
                return response.status_code
            if response.status_code == 429:
                print(f"Rate limited, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                end_time = time.time()
                execution_time = round(end_time - start_time, 6)
                log_entry = f"{start_time:0.0f}, {self.agent},{username},{room_id},{response.status_code},{msg_size},{execution_time}, {whatsuapp_room}"
                self.logger.info(log_entry)
                return response.status_code
        end_time = time.time()
        execution_time = round(end_time - start_time, 6)
        log_entry = f"{start_time:0.0f}, {self.agent}, {username},{room_id},{response.status_code},{msg_size},{execution_time}, {whatsuapp_room}"
        self.logger.info(log_entry)
        return response.status_code

    async def send_message_gen(self, users, message_set):

        for user in tqdm(users):
            access_token = user["access_token"]
            username = user["username"]
            self.set_access_token(access_token)
            list_my_room_id = await self.get_my_rooms()
            print("User: ", username, "Rooms: ", list_my_room_id)
            for item in (list_my_room_id):
                room_id = item['room_id']
                whatsuapp_room = item['whatsuapp_member']

                for i in range(1, random.randint(2, 10)):
                    random_message = random.choice(message_set)
                    ret = await self.send_message(room_id, random_message, username, whatsuapp_room)

    async def register_users_from_csv(self, input_csv, output_csv):
        """Read users from CSV, register them, and save their credentials."""
        try:
            with open(input_csv, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                users = list(reader)

            with open(output_csv, mode="w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["username", "user_id", "access_token"])  # Headers

                for user in tqdm(users):
                    username = user["username"]
                    password = user["password"]
                    response = await self.register_user(username, password)
                    if response.status_code == 200:
                        response = response.json()
                        user_id = response["user_id"]

                        # Log in to get access token
                        login_response = await self.login(username, password)
                        if login_response.status_code == 200:
                            login_response = login_response.json()
                            access_token = login_response["access_token"]

                        # Save user_id and access_token
                        writer.writerow([username, user_id, access_token])
                        self.set_access_token("")
                    elif response.status_code == 400:
                        # Log in to get access token
                        user_id = username+':'+config.DOMAIN
                        print('User already exists, logging in', user_id)
                        login_response = await self.login(username, password)
                        if login_response.status_code == 200:
                            login_response = login_response.json()
                            access_token = login_response["access_token"]
                        # Save user_id and access_token
                        writer.writerow([username, user_id, access_token])
                        self.set_access_token("")

                    else:
                        print(
                            f"Failed to register {username}. Response: {response}")

        except Exception as e:
            print(f"Error reading CSV: {e}")

    def get_user(self, user_list, user_id):
        try:
            filtered_users = list(
                filter(lambda x: x["user_id"] == user_id, user_list))
            # Equivalent to checking len(filtered_users) == 0
            if not filtered_users:
                return None
            return filtered_users[0]['access_token']
        except Exception as e:
            print(f"Error filtering users: {e}")
            return None

    async def get_my_rooms(self):
        endpoint = "/_matrix/client/v3/sync"
        delay = 1
        retries = 5
        for i in range(retries):
            response = await self._request("GET", endpoint)
            if response.status_code == 200:
                data = response.json()
                invited_rooms = data.get("rooms", {}).get("join", {})
                room_list = []
                for i in invited_rooms:
                    whatsuapp_member = False
                    bot_whatsuapp = False
                    for ii in invited_rooms[i]["timeline"]["events"]:
                        if (ii["type"] == "m.room.encrypted") & (ii['sender'] == '@whatsapp-mudita:connect.mudita.com'):
                            bot_whatsuapp = True
                        if (ii["type"] == "m.room.member") & (ii['sender'] == '@whatsapp-mudita:connect.mudita.com'):
                            whatsuapp_member = True
                    if bot_whatsuapp == False:
                        room_list.append(
                            {"room_id": i, "whatsuapp_member": whatsuapp_member})

                return room_list  # Return list of room IDs

            if response.status_code == 429:
                print(f"Rate limited, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                print("❌ Error fetching invites:", response.status_code)
                return []
        return []

    async def get_invited_rooms(self):
        endpoint = "/_matrix/client/v3/sync"
        delay = 1
        retries = 5
        for i in range(retries):
            response = await self._request("GET", endpoint)
            if response.status_code == 200:
                data = response.json()
                invited_rooms = data.get("rooms", {}).get("invite", {})
                return list(invited_rooms.keys())  # Return list of room IDs

            if response.status_code == 429:
                print(f"Rate limited, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                print("❌ Error fetching invites:", response.status_code)
                return []
        return []

    async def accept_invitation(self, room_id):
        endpoint = f"/_matrix/client/v3/rooms/{room_id}/join"
        delay = 1
        retries = 5
        for i in range(retries):
            response = await self._request("POST", endpoint)
            if response.status_code == 200:
                return response
            if response.status_code == 429:
                print(f"Rate limited, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                return response
        return None

    async def accept_all_invitation(self, user_csv, rooms_json):
        try:
            with open(user_csv, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                users = list(reader)

            for user in tqdm(users):
                access_token = user["access_token"]
                username = user["username"]
                self.set_access_token(access_token)
                # print("check invitation for user: ", username)
                invited_rooms = await self.get_invited_rooms()
                if len(invited_rooms) > 0:
                    for room_id in invited_rooms:
                        response = await self.accept_invitation(room_id)
                        if response.status_code != 200:
                            print(
                                f"Failed to accept invitation for user: {username} from room {room_id}")
                # joined_rooms = await self.get_my_rooms()
                # print("Joined rooms: ", joined_rooms)

        except Exception as e:
            print(f"Error reading Files: {e}")

    async def create_dm_rooms(self, user_csv):
        try:
            with open(user_csv, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                users = list(reader)

            for idx, user in tqdm(enumerate(users)):
                n = random.uniform(0.005, 0.05)
                dm_room_peers = [item["user_id"]
                                 for item in helper.select_random_n_percent(users[idx:], n)]

                if (len(dm_room_peers) > 0):
                    user_id = user["user_id"]
                    user_access_token = self.get_user(users, user_id)
                    if user_access_token:
                        for peer in dm_room_peers:

                            self.set_access_token(user_access_token)
                            ret = await self.create_dm_room(peer)
                            if ret.status_code != 200:
                                print(
                                    f"Failed to create DM room between {user_id} and {peer}. Response: {ret.status_code}")
                            break
                    else:
                        print(f"User {user} not found in users list")

        except Exception as e:
            print(f"Error reading Files or other Exception: {e}")

    async def create_rooms_from_csv(self, user_csv, rooms_json,):
        try:
            rooms = {}
            with open(rooms_json, "r", encoding="utf-8") as rooms_jsonfile:
                rooms = json.load(rooms_jsonfile)
            print("Success loading rooms list")

            with open(user_csv, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                users = list(reader)

            for room_name, room_users in tqdm(rooms.items()):

                # print(room_name, room_users)
                owner = room_users[0]
                user_rooms = room_users[1:]

                owner_access_token = self.get_user(users, owner)
                if owner_access_token:
                    self.set_access_token(owner_access_token)
                    ret = await self.create_room(room_name)
                    if ret.status_code == 200:
                        create_root_ret = ret.json()
                        room_id = create_root_ret['room_id']

                        for user in tqdm(user_rooms):
                            response = await self.invite_users(room_id, user)
                    else:
                        print(
                            f"Failed to create room {room_name}. Response: {ret.status_code}")
                else:
                    print(f"Owner {owner} not found in users list")

        except Exception as e:
            print(f"Error reading Files: {e}")

    async def login_users_from_csv(self, input_csv, output_csv):
        """Read users from CSV, login them, and save their credentials."""
        try:
            with open(input_csv, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                users = list(reader)

            with open(output_csv, mode="w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["username", "user_id", "access_token"])  # Headers

                for user in users:
                    username = user["username"]
                    password = user["password"]
                    # print(
                    #     f"Login user: {username} and password: {password}")

                    login_response = await self.login(username, password)
                    # print(f"Login response: {login_response}")
                    if login_response:

                        access_token = login_response.get(
                            "access_token", "N/A") if login_response else "N/A"
                        user_id = login_response.get(
                            "user_id", "N/A") if login_response else "N/A"
                        # Save user_id and access_token
                        writer.writerow([username, user_id, access_token])
                    else:
                        print(
                            f"Failed to login {username}. Response: {login_response}")

        except Exception as e:
            print(f"Error reading CSV: {e}")
