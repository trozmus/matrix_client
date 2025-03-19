import asyncio
from synapse_client import SynapseClient
import config


async def main():
    synapse = SynapseClient(config.BASE_URL)

    # Register users from CSV and store user IDs and access tokens
    await synapse.register_users_from_csv(config.INPUT_CSV, config.OUTPUT_CSV)

    # Close the async client
    await synapse.close()  

# Run the async program
asyncio.run(main())
