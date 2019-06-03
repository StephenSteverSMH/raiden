import pytest

from raiden.tests.utils import factories
from raiden.transfer.mediated_transfer.state import InitiatorPaymentState
from raiden.transfer.mediated_transfer.tasks import InitiatorTask
from raiden.transfer.views import (
    count_token_network_channels,
    detect_balance_proof_change,
    filter_channels_by_partneraddress,
    filter_channels_by_status,
    get_participants_addresses,
    get_token_identifiers,
    get_token_network_addresses,
    get_token_network_registry_by_token_network_address,
    get_transfer_secret,
    role_from_transfer_task,
)


def test_filter_channels_by_partneraddress_empty(chain_state):
    payment_network_address = factories.make_address()
    token_address = factories.make_address()
    partner_addresses = [factories.make_address(), factories.make_address()]
    assert (
        filter_channels_by_partneraddress(
            chain_state=chain_state,
            payment_network_address=payment_network_address,
            token_address=token_address,
            partner_addresses=partner_addresses,
        )
        == []
    )


def test_filter_channels_by_status_empty_excludes():
    channel_states = factories.make_channel_set(number_of_channels=3).channels
    channel_states[1].close_transaction = channel_states[1].open_transaction
    channel_states[2].close_transaction = channel_states[2].open_transaction
    channel_states[2].settle_transaction = channel_states[2].open_transaction
    assert (
        filter_channels_by_status(channel_states=channel_states, exclude_states=None)
        == channel_states
    )


def test_count_token_network_channels_no_token_network(chain_state):
    assert (
        count_token_network_channels(
            chain_state=chain_state,
            payment_network_address=factories.make_address(),
            token_address=factories.make_address(),
        )
        == 0
    )


def test_get_participants_addresses_no_token_network(chain_state):
    assert (
        get_participants_addresses(
            chain_state=chain_state,
            payment_network_address=factories.make_address(),
            token_address=factories.make_address(),
        )
        == set()
    )


def test_get_token_network_registry_by_token_network_address_is_none(chain_state):
    assert (
        get_token_network_registry_by_token_network_address(
            chain_state=chain_state, token_network_address=factories.make_address()
        )
        is None
    )


def test_get_token_network_addresses_empty_list_for_payment_network_none(chain_state):
    assert (
        get_token_network_addresses(
            chain_state=chain_state, payment_network_address=factories.make_address()
        )
        == list()
    )


def test_token_identifiers_empty_list_for_payment_network_none(chain_state):
    assert (
        get_token_identifiers(
            chain_state=chain_state, payment_network_address=factories.make_address()
        )
        == list()
    )


def test_role_from_transfer_task_raises_value_error():
    with pytest.raises(ValueError):
        role_from_transfer_task(object())


def test_get_transfer_secret_none_for_none_transfer_state(chain_state):
    secret = factories.make_secret()
    transfer = factories.create(factories.LockedTransferUnsignedStateProperties(secret=secret))
    secrethash = transfer.lock.secrethash
    payment_state = InitiatorPaymentState(initiator_transfers={secrethash: None}, routes=[])
    task = InitiatorTask(
        token_network_address=factories.UNIT_TOKEN_NETWORK_ADDRESS, manager_state=payment_state
    )
    chain_state.payment_mapping.secrethashes_to_task[secrethash] = task
    assert get_transfer_secret(chain_state=chain_state, secrethash=secrethash) is None


def test_detect_balance_proof_chain_handles_attribute_error(chain_state):
    chain_state.identifiers_to_paymentnetworks["123"] = None
    changes_iterator = detect_balance_proof_change(old_state=object(), current_state=chain_state)
    assert len(list(changes_iterator)) == 0