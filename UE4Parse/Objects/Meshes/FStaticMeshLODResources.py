from typing import List

from UE4Parse.BinaryReader import BinaryStream
from UE4Parse.Objects.EUEVersion import GAME_UE4
from UE4Parse.Objects.FStripDataFlags import FStripDataFlags
from UE4Parse.Objects.Meshes.FColorVertexBuffer import FColorVertexBuffer
from UE4Parse.Objects.Meshes.FRawStaticIndexBuffer import FRawStaticIndexBuffer
from UE4Parse.Objects.Meshes.FStaticMeshVertexBuffer import FStaticMeshVertexBuffer
from UE4Parse.Objects.Meshes.FPositionVertexBuffer import FPositionVertexBuffer
from UE4Parse.Objects.Meshes.FStaticMeshSection import FStaticMeshSection
from UE4Parse.Objects.Meshes.FWeightedRandomSampler import FWeightedRandomSampler

CDSF_AdjancencyData: int = 1
CDSF_MinLodData: int = 2
CDSF_ReversedIndexBuffer: int = 4
CDSF_RaytracingResources: int = 8


class FStaticMeshLODResources:
    stripFlags: FStripDataFlags
    sections: List[FStaticMeshSection]
    vertexBuffer: FStaticMeshVertexBuffer
    positionVertexBuffer: FPositionVertexBuffer
    colorVertexBuffer: FColorVertexBuffer
    indexBuffer: FRawStaticIndexBuffer
    reversedIndexBuffer: FRawStaticIndexBuffer
    depthOnlyIndexBuffer: FRawStaticIndexBuffer
    reversedDepthOnlyIndexBuffer: FRawStaticIndexBuffer
    wireframeIndexBuffer: FRawStaticIndexBuffer
    adjacencyIndexBuffer: FRawStaticIndexBuffer
    maxDeviation: float
    is_lod_cooked_out = False
    inlined = False

    def __init__(self, reader: BinaryStream):
        self.stripFlags = FStripDataFlags(reader)
        self.sections = reader.readTArray_W_Arg(FStaticMeshSection, reader)
        self.maxDeviation = reader.readFloat()

        if reader.game < GAME_UE4(23):
            if not self.stripFlags.isDataStrippedForServer and not self.stripFlags.isClassDataStripped(
                    CDSF_MinLodData):
                self.serializeBuffer_legacy(reader)
            return

        self.is_lod_cooked_out = reader.readBool()
        self.inlined = reader.readBool()

        if not self.stripFlags.isDataStrippedForServer and not self.is_lod_cooked_out:
            if self.inlined:
                self.serializeBuffer(reader)
            else:
                raise NotImplementedError()
        reader.readUInt32()  # SerializedBuffersSize
        reader.readUInt32()  # DepthOnlyIBSize
        reader.readUInt32()  # ReversedIBsSize

    def serializeBuffer_legacy(self, reader: BinaryStream):
        raise NotImplementedError("UE 4.23+ meshes only currently")
        # self.positionVertexBuffer = FPositionVertexBuffer(reader)
        # self.vertexBuffer = FStaticMeshVertexBuffer(reader)

    def serializeBuffer(self, reader: BinaryStream):
        strip_flags = FStripDataFlags(reader)

        self.positionVertexBuffer = FPositionVertexBuffer(reader)
        self.vertexBuffer = FStaticMeshVertexBuffer(reader)
        self.indexBuffer = FRawStaticIndexBuffer(reader)

        if not self.stripFlags.isClassDataStripped(CDSF_ReversedIndexBuffer):
            self.reversedIndexBuffer = FRawStaticIndexBuffer(reader)

        if not self.stripFlags.isEditorDataStripped():
            self.wireframeIndexBuffer = FRawStaticIndexBuffer(reader)

        if not self.stripFlags.isClassDataStripped(CDSF_AdjancencyData):
            self.adjacencyIndexBuffer = FRawStaticIndexBuffer(reader)

        if reader.game >= GAME_UE4(25) and not self.stripFlags.isClassDataStripped(CDSF_RaytracingResources):
            reader.readBulkTArray(reader.readUInt8)  # Raw data

        for i in range(len(self.sections)):
            FWeightedRandomSampler(reader)  # FStaticMeshSectionAreaWeightedTriangleSampler
        FWeightedRandomSampler(reader)  # FStaticMeshAreaWeightedSectionSampler

