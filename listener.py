def scan_blocks(chain, start_block, end_block, contract_address, eventfile='deposit_logs.csv'):

    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    else:
        w3 = Web3(Web3.HTTPProvider(api_url))

    contract_address = Web3.to_checksum_address(contract_address)

    DEPOSIT_ABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "token", "type": "address" }, { "indexed": true, "internalType": "address", "name": "recipient", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "Deposit", "type": "event" }]')

    contract = w3.eth.contract(address=contract_address, abi=DEPOSIT_ABI)

    arg_filter = {}

    if start_block == "latest":
        start_block = w3.eth.get_block_number()
    if end_block == "latest":
        end_block = w3.eth.get_block_number()

    if end_block < start_block:
        print(f"Error end_block < start_block!")
        return

    if start_block == end_block:
        print(f"Scanning block {start_block} on {chain}")
    else:
        print(f"Scanning blocks {start_block} - {end_block} on {chain}")

    if end_block - start_block < 30:
        event_filter = contract.events.Deposit.create_filter(
            from_block=start_block,
            to_block=end_block,
            argument_filters=arg_filter
        )
        events = event_filter.get_all_entries()

        rows = []
        for evt in events:
            row = {
                "chain": chain,
                "token": evt.args["token"],
                "recipient": evt.args["recipient"],
                "amount": evt.args["amount"],
                "transactionHash": evt.transactionHash.hex(),
                "address": evt.address
            }
            rows.append(row)

        if len(rows) > 0:
            df = pd.DataFrame(rows)

            if Path(eventfile).exists():
                df.to_csv(eventfile, mode='a', header=False, index=False)
            else:
                df.to_csv(eventfile, index=False)

    else:
        for block_num in range(start_block, end_block + 1):
            event_filter = contract.events.Deposit.create_filter(
                from_block=block_num,
                to_block=block_num,
                argument_filters=arg_filter
            )
            events = event_filter.get_all_entries()

            for evt in events:
                row = {
                    "chain": chain,
                    "token": evt.args["token"],
                    "recipient": evt.args["recipient"],
                    "amount": evt.args["amount"],
                    "transactionHash": evt.transactionHash.hex(),
                    "address": evt.address
                }

                df = pd.DataFrame([row])

                if Path(eventfile).exists():
                    df.to_csv(eventfile, mode='a', header=False, index=False)
                else:
                    df.to_csv(eventfile, index=False)