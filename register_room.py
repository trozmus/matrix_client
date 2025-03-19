import asyncio
from synapse_client import SynapseClient
import config


async def main():
    synapse = SynapseClient(config.BASE_URL)

    # Register users from CSV and store user IDs and access tokens
    #await synapse.create_rooms_from_csv(config.REGISTERED_USERS_CSV, config.ROOMS_JSON)
    await synapse.create_dm_rooms(config.REGISTERED_USERS_CSV)

    # Close the async client
    await synapse.close()

# Run the async program
asyncio.run(main())
