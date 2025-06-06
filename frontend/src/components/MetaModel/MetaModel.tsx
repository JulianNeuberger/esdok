import React from "react";
import {Background, Controls, Edge, Node, ReactFlow, useEdgesState, useNodesState} from "@xyflow/react";
import {Aspect, Entity, MetaModelService, Relation, MetaModel as MM} from "../../services/metaModelService";
import {Button, Select, Spin} from "antd";
import EntityInput from "../EntityInput/EntityInput";
import RelationInput from "../RelationInput/RelationInput";
import MetaModelEdge from "../MetaModelEdge/MetaModelEdge";
import MetaModelNode from "../MetaModelNode/MetaModelNode";
import Dragger from "antd/es/upload/Dragger";
import {InboxOutlined} from "@ant-design/icons";

const edgeTypes = {"meta-model-edge": MetaModelEdge};
const nodeTypes = {"meta-model-node": MetaModelNode};


const MetaModel = () => {
    const [selectedModel, setSelectedModel] = React.useState<string | undefined>(undefined);
    const [metaModels, setMetaModels] = React.useState<string[]>([]);
    const [isLoading, setIsLoading] = React.useState(false);
    const [hasGraph, setHasGraph] = React.useState(true);
    const [entities, setEntities] = React.useState<Entity[]>([]);
    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
    const [aspects, setAspects] = React.useState<Aspect[]>([]);
    const [newEntity, setNewEntity] = React.useState<Partial<Entity>>({});
    const [newRelation, setNewRelation] = React.useState<Partial<Relation>>({});
    const [umletinoFile, setUmletinoFile] = React.useState<File | undefined>();

    const metaModelService = new MetaModelService();

    React.useEffect(() => {
        const loadMetaModels = async () => {
            setIsLoading(true);
            const models = await metaModelService.listMetaModels();
            setMetaModels(models);
            setIsLoading(false);
        }

        loadMetaModels();
    }, []);

    const load = async () => {
        if(!selectedModel) return;

        setIsLoading(true);
        let modelData: MM | undefined;
        let aspectData: Aspect[];
        try {
            modelData = await metaModelService.loadModel(selectedModel);
            aspectData = await metaModelService.loadAspects(selectedModel);
        } catch (e) {
            setIsLoading(false);
            setHasGraph(false);
            console.log(e);
            return;
        }
        if(typeof modelData === "undefined") {
            setHasGraph(false);
            setIsLoading(false);
            return;
        }

        const entityNodes = modelData.entities.map(e => {
            return {
                id: e.name,
                position: e.position,
                data: {
                    label: e.name,
                    entity: e,
                    aspects: aspectData,
                    metaModel: selectedModel
                },
                dragHandle: ".name",
                type: "meta-model-node"
            };
        });
        const relationEdges = modelData.relations.map(r => {
            return {
                id: r.name,
                source: r.source.name,
                target: r.target.name,
                data: {
                    label: r.name,
                    relation: r,
                    persisted: true,
                    metaModel: selectedModel
                },
                type: "meta-model-edge"
            };
        });

        console.log(relationEdges)

        setEntities(modelData.entities);
        setNodes(entityNodes);
        setEdges(relationEdges);
        // setAspects(aspectData);
        setIsLoading(false);
    }

    React.useEffect(() => {
        const load = async ()=> {
            const modelNames = await metaModelService.listMetaModels();
            setMetaModels(modelNames);
        }

        load();
    }, [])

    React.useEffect(() => {
        load();
    }, [selectedModel])

    const renderFlow = () => {
        if(isLoading) {
            return (
                <div style={{top:0, left:0, right:0, bottom: 0,padding:"50%"}}>
                    <Spin />
                </div>
            );
        }
        if(hasGraph) {
            return (
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={async (connection) => {
                        const source = connection.source;
                        const target = connection.target;

                        const sourceEntity = entities.find(e => e.name == source);
                        const targetEntity = entities.find(e => e.name == target);

                        console.log(sourceEntity, targetEntity)

                        if(!sourceEntity) return;
                        if(!targetEntity) return;

                        const newRelation: Relation = {
                            name: "",
                            description: "",
                            source: sourceEntity,
                            target: targetEntity
                        };

                        await patchModel([], [newRelation]);

                        setEdges([...edges, {
                            id: edges.length.toString(),
                            source: source,
                            target: target,
                            data: {
                                label: "",
                                relation: newRelation,
                                persisted: false,
                                metaModel: selectedModel
                            },
                            type: "meta-model-edge"
                        }]);
                    }}
                    edgeTypes={edgeTypes}
                    nodeTypes={nodeTypes}
                >
                    <Background />
                    <Controls />
                </ReactFlow>
            );
        }
        return (
            <div>No graph, extract now?</div>
        );
    }

    const renderFileUpload = () => {
        return (
            <div key={"file-upload"}>
                <Dragger
                    beforeUpload={(file) => {
                        setUmletinoFile(file);
                        return false;
                    }}
                >
                    <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">Extract graph from file</p>
                    <p className="ant-upload-hint">
                        Drag and drop a UMLetino file here to extract a meta model.
                    </p>
                </Dragger>
                <Button
                    type={"primary"}
                    disabled={!umletinoFile}
                    onClick={async () => {
                        if(!umletinoFile) {
                            console.error("No file set, this should not happen.");
                            return;
                        }
                        if(!selectedModel) return;
                        const file = umletinoFile;
                        setUmletinoFile(undefined);
                        await metaModelService.extract(selectedModel, file);
                        await load();
                    }}
                >
                    Extract
                </Button>
            </div>
        );
    }

    const renderModelSelect = () => {
        return (
            <Select value={selectedModel} onChange={setSelectedModel}>
                {
                    metaModels.map(m => {
                        return (
                            <Select.Option value={m}>{m}</Select.Option>
                        );
                    })
                }
            </Select>
        );
    }

    const patchModel = (entities: Entity[], relations: Relation[]) => {
        if(!selectedModel) return;
        return metaModelService.patchModel(selectedModel, entities, relations);
    }

    const renderNewNodeModal = () => {
        return (
            <div style={{position: "absolute", top: 5, right: 5, width: 250, }}>
                <div>
                    {renderModelSelect()}
                </div>
                <div>
                    {renderFileUpload()}
                </div>
                <div style={{borderRadius: 3, border: "solid 1px black", padding: "5px 15px", backgroundColor: "white", marginBottom: 25}}>
                    <EntityInput
                        key={"entity-input"}
                        aspects={aspects}
                        entity={newEntity}
                        onChange={setNewEntity}
                        onSubmit={(e) => patchModel([e], [])}
                    />
                </div>
                <div style={{borderRadius: 3, border: "solid 1px black", padding: "5px 15px", backgroundColor: "white", marginBottom: 25}}>
                    <RelationInput
                        key={"relation-input"}
                        entities={entities}
                        relation={newRelation}
                        onChange={setNewRelation}
                        onSubmit={(r) => patchModel([], [r])}
                    />
                </div>
            </div>
        );
    }

    return (
        <div style={{ width: '100vw', height: '100vh', position: "relative" }}>
            {renderFlow()}
            {renderNewNodeModal()}
        </div>
    );
}

export default MetaModel;