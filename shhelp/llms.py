import datetime
import os
import pathlib

import beartype
import litellm

litellm.disable_aiohttp_transport = True

_LOG_BASE = pathlib.Path(
    os.getenv("SHHELP_LOGDIR", "~/.local/state/shhelp/logs")
).expanduser()

Message = dict[str, object]
Tool = dict[str, object]


@beartype.beartype
class SessionLogger:
    def __init__(self):
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.dir = _LOG_BASE / ts
        self.dir.mkdir(parents=True, exist_ok=True)
        self._idx = 1

    def log(self, msg: Message) -> None:
        fname = f"{self._idx:02d}.{msg['role']}"
        # content can be None for tool-only assistant msgs
        self.dir.joinpath(fname).write_text(msg["content"] or "")
        self._idx += 1


@beartype.beartype
class Conversation:
    _model: str
    _api_key: str
    _msgs: list[Message]
    _logger: SessionLogger

    def __init__(self, *, model: str, api_key: str):
        self._model = model
        self._api_key = api_key
        self._msgs = []
        self._logger = SessionLogger()

    # Public API
    def system(self, content: str):
        self._push({"role": "system", "content": content})

    def user(self, content: str):
        self._push({"role": "user", "content": content})

    def tool(self, content: str, *, tool_call_id: str):
        self._push({"role": "tool", "content": content, "tool_call_id": tool_call_id})

    async def send(self, *, tools: list[Tool] | None = None):
        resp = await litellm.acompletion(
            model=self._model,
            messages=self._msgs,
            tools=tools,
            api_key=self._api_key,
        )
        msg = resp.choices[0].message
        self._push({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": msg.tool_calls,
        })
        return msg

    def get_costs(self) -> tuple[int, float]:
        usd_per_tok = litellm.model_cost[self._model]["input_cost_per_token"]
        toks_per_msg = [
            litellm.token_counter(model=self._model, messages=[m]) for m in self._msgs
        ]
        usd_per_msg = [usd_per_tok * toks for toks in toks_per_msg]
        usd_total = sum(usd_per_msg)
        toks_total = sum(toks_per_msg)
        return toks_total, usd_total

    # Private API
    def _push(self, msg: Message):
        self._msgs.append(msg)
        self._logger.log(msg)
