import React from "react";
import {Edge, KnowledgeGraphService, Node} from "../services/knowledgeGraph";
import {randomColorScheme} from "../services/colors";
import Dragger from "antd/es/upload/Dragger";
import {DeleteOutlined, InboxOutlined} from "@ant-design/icons";
import {Button, Input, Popconfirm} from "antd";
import InteractiveKnowledgeGraph from "../components/InteractiveKnowledgeGraph/InteractiveKnowledgeGraph";

const knowledgeGraphService = new KnowledgeGraphService();

const KnowledgeGraphView = ()=> {
    const [isLoading, setIsLoading] = React.useState(false);
    const [hasGraph, setHasGraph] = React.useState(true);

    const [nodes, setNodes] = React.useState<Node[]>([]);
    const [edges, setEdges] = React.useState<Edge[]>([]);
    const [highlightedNodes, setHighlightedNodes] = React.useState<Node[]>([]);

    const [colorScheme, setColorScheme] = React.useState<{[k: string]: {textColor: string, backgroundColor: string}}>({});

    const [extractFromFile, setExtractFromFile] = React.useState<File | undefined>();
    const [canExtract, setCanExtract] = React.useState(false);

    const [searchText, setSearchText] = React.useState<string | undefined>();

    React.useEffect(() => {
        load();
    }, []);

    const isNodeRelevant = (node: Node, searchText: string): boolean => {
        if(!searchText) return true;
        if(!node) return false;
        if(node.name == undefined) return false;
        return node.name.toLowerCase().indexOf(searchText.toLowerCase()) !== -1;
    }

    const load = async () => {
        setIsLoading(true);
        let backendData;
        try {
            backendData = await knowledgeGraphService.load();
        } catch (e) {
            setIsLoading(false);
            setHasGraph(false);
        }
        if(typeof backendData === "undefined") {
            setHasGraph(false);
            setIsLoading(false);
            return;
        }
        const aspects = [...new Set(backendData.nodes.map(n => n.aspect))];
        setColorScheme(randomColorScheme(aspects.map(a => a.name)));
        setNodes(backendData.nodes);
        setEdges(backendData.edges);

        setIsLoading(false);
    }

    const renderSearch = () => {
        return (
            <Input
                placeholder={"find nodes..."}
                value={searchText}
                onChange={e => {
                    const newText = e.target.value;
                    setSearchText(newText);
                    setHighlightedNodes(nodes.filter(n => isNodeRelevant(n, newText)));
                }}
            />
        );
    }

    const renderFileUpload = () => {
        return (
            <>
                <Dragger
                    beforeUpload={(file) => {
                        setExtractFromFile(file);
                        setCanExtract(true);
                        return false;
                    }}
                >
                    <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">Extract graph from file</p>
                    <p className="ant-upload-hint">
                        Drag and drop a pdf file here to extract a knowledge graph.
                    </p>
                </Dragger>
                <Button
                    type={"primary"}
                    disabled={!canExtract}
                    onClick={async () => {
                        if(!extractFromFile) {
                            console.error("No file set, this should not happen.");
                            return;
                        }
                        const file = extractFromFile;
                        setCanExtract(false);
                        setExtractFromFile(undefined);
                        await knowledgeGraphService.extract(file);
                        await load();
                    }}
                >
                    Extract
                </Button>
            </>
        );
    }

    const layoutGraph = async () => {
        const success = await knowledgeGraphService.layout();
        await load();
    }


    return (
        <div style={{ width: '100vw', height: '100vh', position: "relative" }}>
            <div style={{width: 250, position: "absolute", top: 5, right: 5, zIndex: 10}}>
                {renderSearch()}
                {renderFileUpload()}
                <Popconfirm
                    title={"Delete knowledge graph"}
                    description={"This will remove the knowledge graph entirely, are you sure?"}
                    onConfirm={async () => {
                        await knowledgeGraphService.delete();
                        await load();
                    }}
                >
                    <Button danger icon={<DeleteOutlined />}>Delete</Button>
                </Popconfirm>
                <Button
                    onClick={layoutGraph}
                    type={"primary"}
                >
                    Layout
                </Button>
            </div>
            <InteractiveKnowledgeGraph
                nodes={nodes}
                edges={edges}
                highlightedNodes={highlightedNodes}
                colorScheme={colorScheme}
            />
        </div>
    );
}

export default KnowledgeGraphView;