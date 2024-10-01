import React from "react";
import {Background, Controls, Edge, Node, ReactFlow, useEdgesState, useNodesState} from "@xyflow/react";
import {Aspect, Entity, MetaModelService, Relation} from "../../services/metaModelService";
import {Button, Form, Input, Select, Spin} from "antd";
import EntityInput from "../EntityInput/EntityInput";
import RelationInput from "../RelationInput/RelationInput";


const MetaModel = () => {
    const [isLoading, setIsLoading] = React.useState(false);
    const [hasGraph, setHasGraph] = React.useState(true);
    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
    const [aspects, setAspects] = React.useState<Aspect[]>([]);
    const [newEntity, setNewEntity] = React.useState<Partial<Entity>>({});
    const [newRelation, setNewRelation] = React.useState<Partial<Relation>>({});

    const metaModelService = new MetaModelService();

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
                position: {
                    x: Math.random() * 500, y: Math.random() * 500
                },
                data: {
                    label: e.name,
                },
            };
        });
        const relationNodes = modelData.relations.map(r => {
            return {
                id: r.name,
                position: {
                    x: Math.random() * 500, y: Math.random() * 500
                },
                data: {
                    label: r.name,
                },
            };
        });
        setNodes(entityNodes.concat(relationNodes))
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

    const renderNewNodeModal = () => {
        return (
            <div style={{position: "absolute", top: 5, right: 5, width: 250, }}>
                <div style={{borderRadius: 3, border: "solid 1px black", padding: "5px 15px", backgroundColor: "white", marginBottom: 25}}>
                    <EntityInput
                        aspects={aspects}
                        entity={newEntity}
                        onChange={setNewEntity}
                        onSubmit={(e) => metaModelService.addToModel([e], [])}
                    />
                </div>
                <div style={{borderRadius: 3, border: "solid 1px black", padding: "5px 15px", backgroundColor: "white", marginBottom: 25}}>
                    <RelationInput
                        relation={newRelation}
                        onChange={setNewRelation}
                        onSubmit={(r) => metaModelService.addToModel([], [r])}
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