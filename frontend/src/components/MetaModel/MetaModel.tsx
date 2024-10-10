import React from "react";
import {Background, Controls, Edge, Node, ReactFlow, useEdgesState, useNodesState} from "@xyflow/react";
import {Aspect, Entity, MetaModelService, Relation} from "../../services/metaModelService";
import {Button, Spin} from "antd";
import EntityInput from "../EntityInput/EntityInput";
import RelationInput from "../RelationInput/RelationInput";
import MetaModelEdge from "../MetaModelEdge/MetaModelEdge";
import MetaModelNode from "../MetaModelNode/MetaModelNode";
import Dragger from "antd/es/upload/Dragger";
import {InboxOutlined} from "@ant-design/icons";


const MetaModel = () => {
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

    const edgeTypes = React.useMemo(() => {
        return {
            "meta-model-edge": MetaModelEdge
        };
    }, []);

    const nodeTypes = React.useMemo(() => {
        return {
            "meta-model-node": MetaModelNode
        };
    }, []);

    const load = async () => {
        setIsLoading(true);
        let modelData;
        let aspectData;
        try {
            modelData = await metaModelService.loadModel();
            aspectData = await metaModelService.loadAspects();
        } catch (e) {
            setIsLoading(false);
            setHasGraph(false);
            console.log(e);
        }
        if(typeof modelData === "undefined") {
            setHasGraph(false);
            setIsLoading(false);
            return;
        }
        if(typeof aspectData === "undefined") {
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
                    entity: e
                },
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
                    persisted: true
                },
                type: "meta-model-edge"
            };
        });

        setEntities(modelData.entities);
        setNodes(entityNodes);
        setEdges(relationEdges);
        setAspects(aspectData);
        setIsLoading(false);
    }

    React.useEffect(() => {
        load();
    }, [])

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

                        await metaModelService.patchModel([], [newRelation]);

                        setEdges([...edges, {
                            id: edges.length.toString(),
                            source: source,
                            target: target,
                            data: {
                                label: "",
                                relation: newRelation,
                                persisted: false
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
            <>
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
                        const file = umletinoFile;
                        setUmletinoFile(undefined);
                        await metaModelService.extract(file);
                        await load();
                    }}
                >
                    Extract
                </Button>
            </>
        );
    }

    const renderNewNodeModal = () => {
        return (
            <div style={{position: "absolute", top: 5, right: 5, width: 250, }}>
                <div>
                    {renderFileUpload()}
                </div>
                <div style={{borderRadius: 3, border: "solid 1px black", padding: "5px 15px", backgroundColor: "white", marginBottom: 25}}>
                    <EntityInput
                        aspects={aspects}
                        entity={newEntity}
                        onChange={setNewEntity}
                        onSubmit={(e) => metaModelService.patchModel([e], [])}
                    />
                </div>
                <div style={{borderRadius: 3, border: "solid 1px black", padding: "5px 15px", backgroundColor: "white", marginBottom: 25}}>
                    <RelationInput
                        entities={entities}
                        relation={newRelation}
                        onChange={setNewRelation}
                        onSubmit={(r) => metaModelService.patchModel([], [r])}
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