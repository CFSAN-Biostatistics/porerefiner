# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: minknow/rpc/keystore.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import google.protobuf.any_pb2
import minknow.rpc.rpc_options_pb2
import minknow.rpc.keystore_pb2


class KeyStoreServiceBase(abc.ABC):

    @abc.abstractmethod
    async def store(self, stream: 'grpclib.server.Stream[minknow.rpc.keystore_pb2.StoreRequest, minknow.rpc.keystore_pb2.StoreResponse]') -> None:
        pass

    @abc.abstractmethod
    async def remove(self, stream: 'grpclib.server.Stream[minknow.rpc.keystore_pb2.RemoveRequest, minknow.rpc.keystore_pb2.RemoveResponse]') -> None:
        pass

    @abc.abstractmethod
    async def get_one(self, stream: 'grpclib.server.Stream[minknow.rpc.keystore_pb2.GetOneRequest, minknow.rpc.keystore_pb2.GetOneResponse]') -> None:
        pass

    @abc.abstractmethod
    async def get(self, stream: 'grpclib.server.Stream[minknow.rpc.keystore_pb2.GetRequest, minknow.rpc.keystore_pb2.GetResponse]') -> None:
        pass

    @abc.abstractmethod
    async def watch(self, stream: 'grpclib.server.Stream[minknow.rpc.keystore_pb2.WatchRequest, minknow.rpc.keystore_pb2.WatchResponse]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/ont.rpc.keystore.KeyStoreService/store': grpclib.const.Handler(
                self.store,
                grpclib.const.Cardinality.UNARY_UNARY,
                minknow.rpc.keystore_pb2.StoreRequest,
                minknow.rpc.keystore_pb2.StoreResponse,
            ),
            '/ont.rpc.keystore.KeyStoreService/remove': grpclib.const.Handler(
                self.remove,
                grpclib.const.Cardinality.UNARY_UNARY,
                minknow.rpc.keystore_pb2.RemoveRequest,
                minknow.rpc.keystore_pb2.RemoveResponse,
            ),
            '/ont.rpc.keystore.KeyStoreService/get_one': grpclib.const.Handler(
                self.get_one,
                grpclib.const.Cardinality.UNARY_UNARY,
                minknow.rpc.keystore_pb2.GetOneRequest,
                minknow.rpc.keystore_pb2.GetOneResponse,
            ),
            '/ont.rpc.keystore.KeyStoreService/get': grpclib.const.Handler(
                self.get,
                grpclib.const.Cardinality.UNARY_UNARY,
                minknow.rpc.keystore_pb2.GetRequest,
                minknow.rpc.keystore_pb2.GetResponse,
            ),
            '/ont.rpc.keystore.KeyStoreService/watch': grpclib.const.Handler(
                self.watch,
                grpclib.const.Cardinality.UNARY_STREAM,
                minknow.rpc.keystore_pb2.WatchRequest,
                minknow.rpc.keystore_pb2.WatchResponse,
            ),
        }


class KeyStoreServiceStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.store = grpclib.client.UnaryUnaryMethod(
            channel,
            '/ont.rpc.keystore.KeyStoreService/store',
            minknow.rpc.keystore_pb2.StoreRequest,
            minknow.rpc.keystore_pb2.StoreResponse,
        )
        self.remove = grpclib.client.UnaryUnaryMethod(
            channel,
            '/ont.rpc.keystore.KeyStoreService/remove',
            minknow.rpc.keystore_pb2.RemoveRequest,
            minknow.rpc.keystore_pb2.RemoveResponse,
        )
        self.get_one = grpclib.client.UnaryUnaryMethod(
            channel,
            '/ont.rpc.keystore.KeyStoreService/get_one',
            minknow.rpc.keystore_pb2.GetOneRequest,
            minknow.rpc.keystore_pb2.GetOneResponse,
        )
        self.get = grpclib.client.UnaryUnaryMethod(
            channel,
            '/ont.rpc.keystore.KeyStoreService/get',
            minknow.rpc.keystore_pb2.GetRequest,
            minknow.rpc.keystore_pb2.GetResponse,
        )
        self.watch = grpclib.client.UnaryStreamMethod(
            channel,
            '/ont.rpc.keystore.KeyStoreService/watch',
            minknow.rpc.keystore_pb2.WatchRequest,
            minknow.rpc.keystore_pb2.WatchResponse,
        )
