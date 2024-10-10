interface Aspect {
    name: string;
    shape: string;
    color: string;
}

export interface Node {
    id: string;
    name: string;
    type: string;
    aspect: Aspect;
    position: {x: number, y: number};
}

export interface Edge {
    id: string;
    type: string;
    source: Node;
    target: Node;
}

export interface KnowledgeGraph {
    nodes: Node[];
    edges: Edge[];
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