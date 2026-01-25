import pytest
from meshcore.adapters.meshtastic.commander import MockCommander
from meshcore.application.ports import CommandResult


@pytest.mark.asyncio
async def test_mock_commander_send_text():
    commander = MockCommander()
    result = await commander.send_text("Test message")
    assert isinstance(result, CommandResult)
    assert result.success is True
    assert "Test message" in result.message


@pytest.mark.asyncio
async def test_mock_commander_send_text_with_destination():
    commander = MockCommander()
    result = await commander.send_text("Hello", destination="!node1234")
    assert result.success is True
    assert "!node1234" in result.message


@pytest.mark.asyncio
async def test_mock_commander_send_text_with_channel():
    commander = MockCommander()
    result = await commander.send_text("Test", channel=1)
    assert result.success is True
    assert "channel 1" in result.message


@pytest.mark.asyncio
async def test_mock_commander_send_position():
    commander = MockCommander()
    result = await commander.send_position(37.7749, -122.4194)
    assert result.success is True
    assert "37.7749" in result.message
    assert "-122.4194" in result.message


@pytest.mark.asyncio
async def test_mock_commander_send_position_with_altitude():
    commander = MockCommander()
    result = await commander.send_position(37.7749, -122.4194, altitude=100)
    assert result.success is True
    assert "100" in result.message


@pytest.mark.asyncio
async def test_mock_commander_send_position_with_destination():
    commander = MockCommander()
    result = await commander.send_position(
        37.7749,
        -122.4194,
        destination="!node1234"
    )
    assert result.success is True
    assert "!node1234" in result.message


@pytest.mark.asyncio
async def test_mock_commander_handles_broadcast():
    commander = MockCommander()
    result = await commander.send_text("Broadcast message", destination=None)
    assert result.success is True
    assert "broadcast" in result.message.lower()

