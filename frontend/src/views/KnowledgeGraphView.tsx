import React from "react";
import {Edge, KnowledgeGraphService, Node} from "../services/knowledgeGraph";
import {randomColorScheme} from "../services/colors";
import Dragger from "antd/es/upload/Dragger";
import {DeleteOutlined, InboxOutlined} from "@ant-design/icons";
import {Button, Form, Input, Popconfirm, Select} from "antd";
import InteractiveKnowledgeGraph from "../components/InteractiveKnowledgeGraph/InteractiveKnowledgeGraph";
import {MetaModelService} from "../services/metaModelService";

const knowledgeGraphService = new KnowledgeGraphService();
const metaModelService = new MetaModelService();

const KnowledgeGraphView = ()=> {
    const [selectedModel, setSelectedModel] = React.useState<string | undefined>(undefined);
    const [metaModels, setMetaModels] = React.useState<string[]>([]);

    const [isLoading, setIsLoading] = React.useState(false);
    const [hasGraph, setHasGraph] = React.useState(true);

    const [nodes, setNodes] = React.useState<Node[]>([]);
    const [edges, setEdges] = React.useState<Edge[]>([]);

    const [colorScheme, setColorScheme] = React.useState<{[k: string]: {textColor: string, backgroundColor: string}}>({});

    const [extractFromFile, setExtractFromFile] = React.useState<File | undefined>();
    const [canExtract, setCanExtract] = React.useState(false);

    const [searchText, setSearchText] = React.useState<string | undefined>();

    React.useEffect(() => {
        const loadMetaModels = async () => {
            setIsLoading(true);
            const models = await metaModelService.listMetaModels();
            setMetaModels(models);
            setIsLoading(false);
        }

        loadMetaModels();
    }, []);

    React.useEffect(() => {
        load();
    }, [selectedModel]);

    const isNodeRelevant = (node: Node, searchText?: string): boolean => {
        if(!searchText) return true;
        if(!node) return false;
        if(node.name == undefined) return false;
        return node.name.toLowerCase().indexOf(searchText.toLowerCase()) !== -1;
    }

    const extractModel = async () => {
        if(!extractFromFile) {
            console.error("No file set, this should not happen.");
            return;
        }
        if(!selectedModel) return;
        const file = extractFromFile;
        setCanExtract(false);
        setExtractFromFile(undefined);
        await knowledgeGraphService.extract(file, selectedModel);
        await load();
    }

    const load = async () => {
        if(selectedModel === undefined) return;

        setIsLoading(true);
        let backendData;
        try {
            backendData = await knowledgeGraphService.load(selectedModel);
        } catch (e) {
            setIsLoading(false);
            setHasGraph(false);
        }
        if(typeof backendData === "undefined") {
            setHasGraph(false);
            setIsLoading(false);
            return;
        }
        const aspects = [...new Set(backendData.nodes.map(n => n.entity.aspect))];
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
                }}
            />
        );
    }

    const renderFileUpload = () => {
        return (
            <Form.Item>
                <Dragger
                    beforeUpload={(file) => {
                        setExtractFromFile(file);
                        setCanExtract(true);
                        return false;
                    }}
                    style={{marginBottom: 5}}
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
                    onClick={extractModel}
                    style={{width: "100%"}}
                >
                    Extract
                </Button>
            </Form.Item>
        );
    }

    const layoutGraph = async () => {
        if(!selectedModel) return;
        const success = await knowledgeGraphService.layout(selectedModel);
        await load();
    }

    const renderContent = ()=> {
        if(hasGraph) {
            return (
                <InteractiveKnowledgeGraph
                    nodes={nodes}
                    edges={edges}
                    highlightedNodes={nodes.filter(n => isNodeRelevant(n, searchText))}
                    colorScheme={colorScheme}
                />
            );
        }

        return (
            <div
                style={{
                    width: 350,
                    margin: "auto",
                    paddingTop: 350
                }}
            >
                <Form>
                    <Form.Item>
                        <h3 style={{textAlign: "center"}}>
                            No graph, create one now?
                        </h3>
                    </Form.Item>
                    <Form.Item>
                        {renderFileUpload()}
                    </Form.Item>
                </Form>
            </div>
        );
    }

    const renderMetaModelSelect = () => {
        return (
            <Form.Item
                label={"meta model"}
                labelCol={{span: 24}}
            >
                <Select
                    value={selectedModel}
                    style={{width: "100%"}}
                    onChange={(e) => (console.log(e),setSelectedModel(e))}
                >
                    {
                        metaModels.map(m => {
                            return (
                                <Select.Option value={m}>
                                    {m}
                                </Select.Option>
                            );
                        })
                    }
                </Select>
            </Form.Item>
        );
    }

    const renderOptions = () => {
        return (
            <div style={{width: 250, position: "absolute", top: 5, right: 5, zIndex: 10, backgroundColor: "white", padding: 5, border: "solid 1px #ccc", borderRadius: 5}}>
                <Form>
                    {renderMetaModelSelect()}
                    {renderFileUpload()}
                    <Form.Item>
                        <Popconfirm
                            title={"Delete knowledge graph"}
                            description={"This will remove the knowledge graph entirely, are you sure?"}
                            onConfirm={async () => {
                                if(!selectedModel) return;
                                await knowledgeGraphService.delete(selectedModel);
                                setNodes([]);
                                setEdges([]);
                                setColorScheme({});
                                setHasGraph(false);
                            }}
                        >
                            <Button danger icon={<DeleteOutlined />} style={{width: "100%"}}>Delete</Button>
                        </Popconfirm>
                    </Form.Item>
                    <Form.Item>
                        <Button
                            onClick={layoutGraph}
                            style={{width: "100%"}}
                        >
                            Layout
                        </Button>
                    </Form.Item>
                </Form>
            </div>
        );
    }

    return (
        <div style={{ width: '100vw', height: '100vh', position: "relative" }}>
            <div style={{width: 500, position: "absolute", top: 5, transform: "translate(-50%, 0)", left: "50%", zIndex: 10}}>
                {renderSearch()}
            </div>
            {renderOptions()}
            {renderContent()}
        </div>
    );
}

export default KnowledgeGraphView;