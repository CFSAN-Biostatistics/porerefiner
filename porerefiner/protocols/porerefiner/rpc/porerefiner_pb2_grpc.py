# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from porerefiner.protocols.porerefiner.rpc import porerefiner_pb2 as porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2


class PoreRefinerStub(object):
    """Missing associated documentation comment in .proto file"""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetRuns = channel.unary_unary(
                '/porerefiner.rpc.PoreRefiner/GetRuns',
                request_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunListRequest.SerializeToString,
                response_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunListResponse.FromString,
                )
        self.GetRunInfo = channel.unary_unary(
                '/porerefiner.rpc.PoreRefiner/GetRunInfo',
                request_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRequest.SerializeToString,
                response_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunResponse.FromString,
                )
        self.AttachSheetToRun = channel.unary_unary(
                '/porerefiner.rpc.PoreRefiner/AttachSheetToRun',
                request_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunAttachRequest.SerializeToString,
                response_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.GenericResponse.FromString,
                )
        self.RsyncRunTo = channel.unary_unary(
                '/porerefiner.rpc.PoreRefiner/RsyncRunTo',
                request_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRsyncRequest.SerializeToString,
                response_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRsyncResponse.FromString,
                )
        self.Tag = channel.unary_unary(
                '/porerefiner.rpc.PoreRefiner/Tag',
                request_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.TagRequest.SerializeToString,
                response_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.GenericResponse.FromString,
                )


class PoreRefinerServicer(object):
    """Missing associated documentation comment in .proto file"""

    def GetRuns(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetRunInfo(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AttachSheetToRun(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RsyncRunTo(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Tag(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PoreRefinerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetRuns': grpc.unary_unary_rpc_method_handler(
                    servicer.GetRuns,
                    request_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunListRequest.FromString,
                    response_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunListResponse.SerializeToString,
            ),
            'GetRunInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.GetRunInfo,
                    request_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRequest.FromString,
                    response_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunResponse.SerializeToString,
            ),
            'AttachSheetToRun': grpc.unary_unary_rpc_method_handler(
                    servicer.AttachSheetToRun,
                    request_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunAttachRequest.FromString,
                    response_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.GenericResponse.SerializeToString,
            ),
            'RsyncRunTo': grpc.unary_unary_rpc_method_handler(
                    servicer.RsyncRunTo,
                    request_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRsyncRequest.FromString,
                    response_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRsyncResponse.SerializeToString,
            ),
            'Tag': grpc.unary_unary_rpc_method_handler(
                    servicer.Tag,
                    request_deserializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.TagRequest.FromString,
                    response_serializer=porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.GenericResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'porerefiner.rpc.PoreRefiner', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class PoreRefiner(object):
    """Missing associated documentation comment in .proto file"""

    @staticmethod
    def GetRuns(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/porerefiner.rpc.PoreRefiner/GetRuns',
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunListRequest.SerializeToString,
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunListResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetRunInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/porerefiner.rpc.PoreRefiner/GetRunInfo',
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRequest.SerializeToString,
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AttachSheetToRun(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/porerefiner.rpc.PoreRefiner/AttachSheetToRun',
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunAttachRequest.SerializeToString,
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.GenericResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RsyncRunTo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/porerefiner.rpc.PoreRefiner/RsyncRunTo',
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRsyncRequest.SerializeToString,
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.RunRsyncResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Tag(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/porerefiner.rpc.PoreRefiner/Tag',
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.TagRequest.SerializeToString,
            porerefiner_dot_protocols_dot_porerefiner_dot_rpc_dot_porerefiner__pb2.GenericResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)
