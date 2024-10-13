import React from "react";

import {Node as KgNode} from "../../services/knowledgeGraph";
import {Handle, Position} from "@xyflow/react";

import "./KnowledgeGraphNode.css";


export interface Props {
    data: {
        node: KgNode,
        color?: string;
        backgroundColor?: string;
        shape?: "rounded" | "rect" | "parallelogram"
    }
}


const KnowledgeGraphNode = ({data}: Props) => {
    const node = data.node;
    const shape = data.shape || "rounded";
    console.log(shape)

    return (
        <div
            className={`node ${shape}`}
            style={{
                color: data.color,
            }}
        >
            <div
                className={`shape ${shape}`}
                style={{
                    color: data.color,
                    backgroundColor: data.backgroundColor,
                    borderColor: data.color
                }}
            />
            <Handle type={"source"} position={Position.Top} />
            <Handle type={"target"} position={Position.Top} />
            <div style={{fontStyle: "italic", fontWeight: "bold", fontSize: ".7em"}}>
                {node.type}
            </div>
            <div>
                {node.name}
            </div>
        </div>
    );
}

export default KnowledgeGraphNode;