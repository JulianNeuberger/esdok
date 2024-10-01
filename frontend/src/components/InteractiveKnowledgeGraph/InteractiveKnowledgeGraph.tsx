import React from "react";
import {Background, Controls, Edge, Node, ReactFlow, useEdgesState, useNodesState} from "@xyflow/react";
import {KnowledgeGraphService} from "../../services/knowledgeGraph";

import '@xyflow/react/dist/style.css';
import {randomColorScheme, randomColorSet} from "../../services/colors";
import {Input, Spin} from "antd";

const InteractiveKnowledgeGraph = () => {
    const [isLoading, setIsLoading] = React.useState(false);
    const [hasGraph, setHasGraph] = React.useState(true);
    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

    const [searchText, setSearchText] = React.useState<string | undefined>();

    const load = async () => {
        setIsLoading(true);
        let backendData;
        try {
            backendData = await knowledgeGraphService.load();
        } catch (e) {
            setIsLoading(false);
            setHasGraph(false);
            console.log(e);
        }
        if(typeof backendData === "undefined") {
            setHasGraph(false);
            setIsLoading(false);
            return;
        }
        const aspects = [...new Set(backendData.nodes.map(n => n.aspect))];
        const colorScheme = randomColorScheme(aspects);
        setEdges(backendData.edges.map(e => {
            console.log(e)
            return {
                id: e.id,
                source: e.source,
                target: e.target,
                label: e.name
            };
        }));
        setNodes(backendData.nodes.map(n => {
            const {textColor, backgroundColor} = colorScheme[n.aspect];
            console.log(n)
            return {
                id: n.id,
                position: {
                    x: Math.random() * 500, y: Math.random() * 500
                },
                data: {
                    label: n.name,
                },
                style: {
                    color: textColor,
                    backgroundColor: backgroundColor,
                    borderWidth: 1
                }
            };
        }));
        setIsLoading(false);
    }

    const highlightNodes = (toHighlight: Node[]) => {
        const newNodes = nodes.map(n => {
            if(toHighlight.indexOf(n) !== -1) {
                console.log("highlighting...")
                return {
                    ...n,
                    style: {
                        ...n.style,
                        borderWidth: 3
                    }
                };
            } else {
                return {
                    ...n,
                    style: {
                        ...n.style,
                        borderWidth: 1
                    }
                };
            }
        });
        setNodes(newNodes);
    }

    const findNodes = (predicate: (node: Node) => boolean): Node[] => {
        return nodes.filter(predicate);
    }

    React.useEffect(() => {
        load();
    }, []);

    const knowledgeGraphService = new KnowledgeGraphService();

    const isNodeRelevant = (node: Node, searchText: string): boolean => {
        if(node.data.label == undefined) return false;
        if(!(typeof node.data.label === "string")) return false;
        return node.data.label.toLowerCase().indexOf(searchText.toLowerCase()) !== -1;
    }

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

    return (
        <div style={{ width: '100vw', height: '100vh', position: "relative" }}>
            <div style={{width: 250, position: "absolute", top: 5, right: 5, zIndex: 10}}>
                <Input
                    placeholder={"find nodes..."}
                    value={searchText}
                    onChange={e => {
                        const newText = e.target.value;
                        setSearchText(newText);

                        if(newText.length == 0) {
                            highlightNodes([]);
                        } else {
                            const toHighlight = findNodes(n => isNodeRelevant(n, newText));
                            highlightNodes(toHighlight);
                        }
                    }}
                />
            </div>
            {renderFlow()}
        </div>
    );
}

export default InteractiveKnowledgeGraph;