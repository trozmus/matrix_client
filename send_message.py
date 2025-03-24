import asyncio
import time
from synapse_client import SynapseClient
import config
import helper
import argparse


async def main():
    parser = argparse.ArgumentParser(
        description="Generates messages by users ")
    parser.add_argument("num_users", type=int, default=200, nargs="?",
                        help="Number of users")

    parser.add_argument("-a", "--agent", type=str, default="agent1", nargs="?",
                        help="Agent Name")
    args = parser.parse_args()

    users = helper.get_users_from_csv(config.REGISTERED_USERS_CSV)
    n = args.num_users/(len(users))

    users_set = helper.select_random_n_percent(users, n)
    users_set = users[:5]
    log_filename = args.agent + "_" + time.strftime("%Y%m%d-%H%M%S") + ".csv"
    logger = helper.setup_logger(log_filename)

    # Register users from CSV and store user IDs and access tokens
    synapse = SynapseClient(config.BASE_URL, logger=logger, agent=args.agent)

    for i in range(20):
        await synapse.send_message_gen(users_set, helper.message_set)

    # Close the async client
    await synapse.close()

# Run the async program
asyncio.run(main())
