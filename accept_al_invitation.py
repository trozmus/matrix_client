import asyncio
from synapse_client import SynapseClient
import config



async def main():
    synapse = SynapseClient(config.BASE_URL)

    # Register users from CSV and store user IDs and access tokens
    await synapse.accept_all_invitation(config.REGISTERED_USERS_CSV, config.ROOMS_JSON)

    # Close the async client
    await synapse.close()

# Run the async program
asyncio.run(main())
