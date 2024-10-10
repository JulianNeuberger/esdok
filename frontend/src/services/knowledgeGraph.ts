export interface KnowledgeGraphNode {
    id: string;
    name: string;
    aspect: string;
}

export interface KnowledgeGraphEdge {
    id: string;
    source: string;
    target: string;
    name?: string;
}

export interface KnowledgeGraph {
    nodes: KnowledgeGraphNode[];
    edges: KnowledgeGraphEdge[];
}

export class KnowledgeGraphService {

    public constructor() {

    }

    public load = async (): Promise<KnowledgeGraph | undefined> => {
        const response = await fetch(" http://127.0.0.1:5000/graph/");
        const json = await response.json();
        if(!Object.hasOwn(json, "nodes")) {
            return undefined;
        }
        if(!Object.hasOwn(json, "edges")) {
            return undefined;
        }
        return json;
    }

    public extract = async (file: File): Promise<boolean> => {
        const data = new FormData();
        data.append("file", file);

        const response = await fetch(" http://127.0.0.1:5000/graph/extract", {
            method: "POST",
            body: data
        });

        const json = await response.json();
        return json["success"];
    }
}