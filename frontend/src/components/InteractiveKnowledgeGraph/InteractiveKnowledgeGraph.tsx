import React from "react";
import {Background, Controls, Edge, Node, ReactFlow, useEdgesState, useNodesState} from "@xyflow/react";
import {Edge as KgEdge, Node as KgNode} from "../../services/knowledgeGraph";

import '@xyflow/react/dist/style.css';
import KnowledgeGraphNode, {Props as KnowledgeGraphNodeProps} from "../KnowledgeGraphNode/KnowledgeGraphNode";

const nodeTypes = {"kg-node": KnowledgeGraphNode};

interface Props {
    nodes: KgNode[];
    edges: KgEdge[];
    highlightedNodes: KgNode[];
    colorScheme: {[aspectName: string]: {textColor: string, backgroundColor: string}};
}

const InteractiveKnowledgeGraph = (props: Props) => {
    const [nodes, setNodes, onNodesChange] = useNodesState<Node<KnowledgeGraphNodeProps["data"]>>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

    const isHighlighted = (node: KgNode) => {
        if(props.highlightedNodes === undefined) return true;
        if(props.highlightedNodes.findIndex(x => x.id === node.id) !== -1) return true;
        return false;
    }

    React.useEffect(() => {
        setEdges(props.edges.map(e => {
            return {
                id: e.id,
                source: e.source.id,
                target: e.target.id,
                label: e.type
            };
        }));
        setNodes(props.nodes.map(n => {
            const {textColor, backgroundColor} = props.colorScheme[n.entity.aspect.name];
            return {
                id: n.id,
                position: {
                    x: n.position.x * 2,
                    y: n.position.y * 2
                },
                data: {
                    node: n,
                    color: textColor,
                    backgroundColor: backgroundColor,
                    shape: n.entity.aspect.shape,
                    opacity: isHighlighted(n) ? 1.0 : 0.5
                },
                type: "kg-node"
            };
        }));
    }, [props.nodes, props.edges, props.highlightedNodes]);

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
        >
            <Background />
            <Controls />
        </ReactFlow>
    );
}

export default InteractiveKnowledgeGraph;