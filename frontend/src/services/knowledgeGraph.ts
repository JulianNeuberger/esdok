export interface KnowledgeGraphNode {
    id: string;
    name: string;
    aspect: string;
}

export interface KnowledgeGraphEdge {
    id: string;
    sourceId: string;
    targetId: string;
    name?: string;
}

export interface KnowledgeGraph {
    nodes: KnowledgeGraphNode[];
    edges: KnowledgeGraphEdge[];
}

export class KnowledgeGraphService {

    public constructor() {

    }

    public load = async (): Promise<KnowledgeGraph> => {
        return {
            nodes: [
                {id: "n1", name: "Martin K.", aspect: "organizational"},
                {id: "n2", name: "Julian N.", aspect: "organizational"},
                {id: "n3", name: "Uni Bayreuth", aspect: "organizational"},
                {id: "n4", name: "TU Wien", aspect: "organizational"},
                {id: "n5", name: "Stefan B.", aspect: "organizational"},
            ],
            edges: [
                {id: "e1", sourceId: "n1", targetId: "n3", name: "employed at"},
                {id: "e2", sourceId: "n2", targetId: "n3", name: "employed at"},
                {id: "e3", sourceId: "n5", targetId: "n4", name: "employed at"},
                {id: "e4", sourceId: "n3", targetId: "n4", name: "cooperate"},
            ],
        }
    }
}